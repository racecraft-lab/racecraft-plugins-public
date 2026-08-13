---
topic: "Scaffold Integration — blind-spot pass and autopilot chain"
slug: "art-011-scaffold-integration"
date: "2026-08-12"
mode: "setup"
spec_id: "ART-011"
source_input:
  type: "topic"
  ref: "docs/ai/specs/html-artifacts-technical-roadmap.md § ART-011: Scaffold Integration"
question_count: 21
stop_reason: "natural"
---

# Design Concept: Scaffold Integration — blind-spot pass and autopilot chain

> **Source:** `docs/ai/specs/html-artifacts-technical-roadmap.md` § ART-011
> **Date:** 2026-08-12
> **Questions asked:** 21
> **Stop reason:** natural — every queued branch closed, confirmed at a checkpoint
> **Size estimate (advisory):** `estimate-spec-size` with 4 user stories, 2 files,
> 13 FRs, modify-weighted returns `{estimated_loc: 187, suggested_slices: 1,
> status: "ok"}` — under the 400 ceiling, one vertical slice, no split warranted.
> The roadmap's own declaration is 162 LOC over ~4 production files; the
> interview reduced the production surface to the two scaffold `SKILL.md`
> variants, so the file count is now the lower bound of that range.

## Goals

- Make scaffold the single front door: a read-only blind-spot pass runs before
  grill-me, and after everything scaffold owns is committed and pushed, the run
  chains into the autopilot plan stage behind one explicit confirmation.
- Execute the blind-spot pass by dispatching the already-shipped read-only
  `codebase-analyst` on both platforms, so "read-only" is a tool restriction
  rather than a promise, and no new agent definition is added (Q2).
- Seed findings into the interview through the `scope` argument grill-me already
  consumes, leaving grill-me's machinery untouched (Q3).
- Ship one vertical slice: blind-spot pass → interview seeding → chain hand-off →
  closing report, across both platform variants.
- Keep the production surface at exactly two files —
  `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` and
  `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md`.
- Ship against ART-006 alone. The closing report renders the draft-PR URL when
  the plan stage produced one and omits that line with a plain note when it did
  not, so ART-007 is not a blocking dependency (Q1).

## Non-goals

- **A draft-PR producer.** ART-011 does not create the draft PR whose URL its
  report can show; that is ART-007 — answered in Q1 (PR-URL gap).
- **Any change to grill-me.** No new argument, no output-schema change, no
  machinery edit — answered in Q3 (Seeding) and Q19 (Doc schema).
- **A new agent definition.** Neither a Claude `agents/*.md` nor a Codex
  `codex-agents/*.toml` is added or edited, which also keeps the Layer 6 sha256
  corpus chain unstaled — answered in Q2 (Pass engine).
- **A separate findings artifact.** No `.process/<SPEC-ID>-blind-spots.md`;
  findings live in the design concept only — answered in Q8 (Findings home).
- **Widening scaffold's `allowed-tools`.** No Grep, Glob, or Bash grant —
  answered in Q2 (Pass engine).
- **Normalizing the `Key Files` heading across the eleven roadmaps.** The pass
  degrades instead — answered in Q12 (Missing seed).
- **A skip flag for the pass.** Mandatory, mirroring grill-me's own hard
  constraint — answered in Q17 (Skippable?).
- **New executable machinery or a runner helper to render the report.** Every
  change is prose — answered in Q21 (Verification).

## Design Tree (Q&A log)

### Q1. ART-011's closing report is specified to show a draft-PR URL, but ART-007 has not shipped — nothing creates that PR today. How should ART-011 handle the missing producer?

**Branch:** Dependencies

**Recommended answer:** Conditional report — render the URL when the plan stage
produced one, omit the line with a plain note when it did not.
> House precedent is exact. ART-006 deferred its own `gh` corroboration limb to
> ART-007 for this reason: "during ART-006 no draft PR exists, so the branch has
> no live input and only its negative case is testable"
> (`docs/ai/specs/html-artifacts-technical-roadmap.md:451-460`). Keeps ART-011's
> dependency at ART-006 only, which is what makes it Ready today.

**Alternatives offered:**
- Add ART-007 as a hard dependency: simpler report logic and matches the stated
  execution order, but blocks the pass and the chain — neither of which needs a
  PR — behind unrelated work.
- Drop the URL from ART-011 entirely: narrowest slice, but splits one report
  across two specs and leaves AC-11.3 partly unmet.

**User's answer:** Conditional report (Recommended)

---

### Q2. Scaffold's declared `allowed-tools` is `Read Edit Write Skill Agent ToolSearch` — no Grep, Glob, or Bash. How should the read-only blind-spot pass execute?

**Branch:** Architecture / tool scoping

**Recommended answer:** Dispatch the shipped read-only `codebase-analyst`,
unmodified.
> `speckit-pro/agents/codebase-analyst.md` and
> `speckit-pro/codex-agents/codebase-analyst.toml` both exist and are restricted
> to read tools (no Write/Edit/MultiEdit); the Codex autopilot already spawns it
> (`speckit-pro/codex-skills/speckit-autopilot/references/phase-execution-codex.md:244`).
> Scaffold already holds `Agent`. Read-only becomes provable, both platforms get
> one engine, and no agent file is edited — which also avoids restaling the
> Layer 6 sha256 corpus chain that any agent edit triggers.

**Alternatives offered:**
- Widen `allowed-tools` and scan inline: fewer moving parts, but "read-only"
  becomes an unenforced promise inside a session holding Write and Edit.
- New dedicated blind-spot agent: best-fit prompt, but two new production files
  against a ~4-file budget plus untooled Layer 6 digest regeneration.

**User's answer:** Dispatch to codebase-analyst (Recommended)

---

### Q3. Roadmap marks grill-me "input only, no machinery change". How should findings reach the interview and the design concept's Open Questions?

**Branch:** Interfaces

**Recommended answer:** Append a labelled findings block to the `scope` argument
scaffold already passes.
> Both grill-me variants document "Input: the spec scope description from the
> technical roadmap" (`speckit-pro/skills/grill-me/SKILL.md` and
> `speckit-pro/codex-skills/grill-me/SKILL.md:129`), so the channel exists and
> neither file is edited. Honours "no machinery change" literally and holds the
> production count at two.

**Alternatives offered:**
- A documented `blind_spots` argument: explicit contract, but two more
  production files and it edits the one skill the roadmap said not to change.
- Scaffold appends to Open Questions afterwards: guarantees the doc record, but
  findings never reach the interview — the half of AC-11.1 that matters.

**User's answer:** Fold into the existing scope arg (Recommended)

---

### Q4. After the workflow-file commit, how should scaffold hand off to the autopilot plan stage?

**Branch:** Architecture

**Recommended answer:** In-session `Skill()` invocation with
`<workflow-file> --stage plan`.
> The per-platform invocation form is fixed by the ART-006 chain contract §3.
> Scaffold already holds `Skill`, and autopilot is built to absorb the context
> cost: `speckit-pro/skills/speckit-autopilot/SKILL.md:51` says the window
> auto-compacts and to complete every phase anyway, with the workflow file as
> the durable record (`:774`, `:795-796`). This is what delivers "one
> invocation ends at the reviewed draft PR".

**Alternatives offered:**
- Print the command for the operator to re-run: cheapest context and a clean
  seam, but a hand-off rather than a chain — AC-11.2 unmet.
- Spawn autopilot as a subagent: isolates context, but nests agents two deep
  and autopilot's gates assume a real session.

**User's answer:** In-session Skill() invocation (Recommended)

---

### Q5. Where does the new closing report sit relative to the existing "Scaffold Complete" report and the chain confirmation?

**Branch:** Operator experience

**Recommended answer:** Keep both. The existing report prints after the
workflow-file commit; the closing report renders once the chain resolves.
> A confirmation with no context is not a real choice, and ART-006's key
> decision requires "a visible seam". On accept the closing report follows the
> plan stage; on decline it prints immediately, with the PR line present or
> absent per Q1.

**Alternatives offered:**
- Single merged report at the end: less output, but the operator confirms the
  chain having been told nothing about what scaffold produced.
- Closing report before the confirmation only: clean ownership, but it cannot
  carry the PR URL or the post-plan artifact index — AC-11.3 unmet.

**User's answer:** Keep both; closing report after the chain (Recommended)

---

### Q6. What should the blind-spot pass be pointed at?

**Branch:** Behavior / scope

**Recommended answer:** The roadmap entry's Key Files and Scope text, plus an
explicit requirement to chase the entry's `Depends On` specs into git history
for artifacts the archive sweep removed.
> This scaffold run proved the need. ART-011's normative input is ART-006's
> FR-016 chain contract, which was deleted at archive time and exists only at
> `git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`.
> No Key Files entry names it. Bounding the seed while leaving the reach open is
> what lets the pass find unknown unknowns rather than confirm known ones.

**Alternatives offered:**
- Key Files and Scope only: deterministic and cheap, but cannot find anything
  the roadmap author already failed to think of.
- Broad repo-wide sweep: widest net, but unbounded cost and findings diluted by
  irrelevant material.

**User's answer:** Key Files + Scope + archived-dependency history (Recommended)

---

### Q7. Once scaffold chains into autopilot, how should the description's "Not for ... running a populated workflow" boundary be reworded?

**Branch:** Trigger surface / routing

**Recommended answer:** Keep the boundary; add the new capability to the
capability sentence.
> The disambiguation stays true: autopilot remains the right entry point for an
> existing workflow file, and the chain is an internal consequence of
> scaffolding a new one, not a routing change. Descriptions are what routing
> matches on, and scaffold already appears as a negative case in the install,
> upgrade, prd, and grill-me fixtures under
> `tests/speckit-pro/layer2-trigger/evals/` and `codex-evals/` — loosening the
> boundary risks all of them.

**Alternatives offered:**
- Rewrite scaffold as "the single front door": best framing of the new flow,
  but invites "run my workflow file" prompts to route to scaffold.
- Leave the description untouched: zero routing risk, but the capability is
  undiscoverable and the roadmap's verification line expects a reworded
  description.

**User's answer:** Keep the boundary, add the new capability (Recommended)

---

### Q8. Should the raw findings be preserved as their own artifact, or live only inside the design concept?

**Branch:** Artifacts / data

**Recommended answer:** Design concept only.
> The roadmap names exactly one destination — "seed them into grill-me and the
> design concept's Open Questions". Grill-me already writes that doc, so there
> is no new write step, no new file against the budget, and no second record to
> drift. Constitution VI (KISS, Simplicity & YAGNI) points the same way.

**Alternatives offered:**
- Separate `.process/` exhaust artifact following ART-012's "notes are exhaust"
  precedent: preserves findings the interview never reached, but duplicates the
  record.
- Both: nothing lost, most drift surface.

**User's answer:** Design concept only (Recommended)

---

### Q9. Step 8 commits the roadmap status flip after the workflow-file commit. Chaining "after the workflow-file commit" would skip it. Where does the chain go?

**Branch:** Sequencing

**Recommended answer:** After Step 8, once everything scaffold owns is committed
and pushed.
> Step 8 is also after the workflow-file commit, so the roadmap's wording is
> satisfied and nothing is skipped. A chained plan stage that fails or is
> interrupted otherwise leaves the roadmap claiming the spec is still Ready.

**Alternatives offered:**
- Immediately after Step 7, autopilot inherits Step 8: fastest to planning, but
  moves a scaffold-owned roadmap edit into autopilot's scope, which no ART-006
  contract covers.
- Chain after Step 7 and re-run Step 8 afterwards: richer status line, but the
  roadmap is wrong for the whole plan stage and never reconciles if the session
  dies.

**User's answer:** After Step 8, once everything scaffold owns is pushed (Recommended)

---

### Q10. If the chained plan stage fails, stalls, or is interrupted, what should the closing report say?

**Branch:** Error paths

**Recommended answer:** Read completion from the workflow file.
> ART-006 §4 exists for exactly this: planning completion is observable from the
> workflow file alone — terminal status on every planning row plus a recorded
> G6.5 verdict — with no live session and no state file. The report states which
> phases reached terminal status, omits the PR line when there is no PR, and
> names the resume command. The contract also requires reading the shipped
> `WORKFLOW_TERMINAL_STATUSES` frozenset in
> `speckit-pro/skills/speckit-autopilot/scripts/validate-autopilot-phase-coverage.py`
> rather than re-declaring the six status literals.

**Alternatives offered:**
- Report only on success: clean ownership, but the operator is left at an
  autopilot error with no statement of what was committed or how to resume.
- Generic failure line: cheap, but cannot distinguish a run that died in Specify
  from one that died at the confidence gate.

**User's answer:** Read completion from the workflow file (Recommended)

---

### Q11. If no structured confirmation tool is available, what should the chain do?

**Branch:** Platform parity / error paths

**Recommended answer:** Do not chain; print the hand-off command.
> ART-006's key decision is that scaffold auto-continues "after an explicit
> confirmation, preserving the interactive/autonomous boundary at a visible
> seam". A chain that starts without a real confirmation crosses that boundary
> silently. Everything scaffold owns is already committed and pushed by then, so
> the operator loses one command, not any work. Claude uses `AskUserQuestion`;
> Codex uses `request_user_input` when present
> (`speckit-pro/codex-skills/grill-me/SKILL.md:283-286`).

**Alternatives offered:**
- Free-text fallback mirroring grill-me's own last resort: keeps the one-command
  flow alive, but a misparsed reply starts an unapproved autonomous run.
- Chain by default when confirmation is unavailable: inverts ART-006's decision
  in exactly the unattended case where it is most expensive.

**User's answer:** Do not chain; print the hand-off command (Recommended)

---

### Q12. The `Key Files` heading is not standardized across this repo's roadmaps. What should the pass do when the seed section is missing or differently named?

**Branch:** Behavior / robustness

**Recommended answer:** Treat `Key Files` as an optional hint; make the Scope
text and the `Depends On` chain the required seed.
> Measured across the eleven roadmaps in `docs/ai/specs/`: html-artifacts uses
> `**Key Files:**`, cross-platform-plugin-runtime uses `**Key Files To Audit:**`
> and `**Key Files Likely To Change:**`, harness-engineering-uplift has the
> section on 9 of 15 entries, and pr-size-governance has none at all across its
> 14 PRSG entries. Scope and `Depends On` are present in every entry of all
> eleven. The pass then works everywhere today without editing any roadmap, and
> degrades in quality rather than failing.

**Alternatives offered:**
- Require Key Files, report a gap and skip: forces roadmap hygiene, but leaves
  the feature dark on all 14 PRSG entries and every renamed heading.
- Standardize the heading as part of ART-011: fixes the root cause, but is a
  wide docs edit outside a harness slice, and roadmap prose is speckit-coach's.

**User's answer:** Key Files is an optional hint (Recommended)

---

### Q13. How many findings should the pass surface?

**Branch:** Behavior / cost

**Recommended answer:** Top 5, ranked by impact and surprise, always stating how
many were set aside.
> Five is small enough to seed an interview whose own soft cap is 30 questions,
> and autopilot already instructs subagents to keep summaries concise
> (`speckit-pro/skills/speckit-autopilot/SKILL.md:795`). A truncation the
> operator cannot see reads as "that was everything", so the omitted count is
> part of the contract, not a nicety. The operator can ask for the rest.

**Alternatives offered:**
- No cap: maximum recall, but the scope string grows without bound and a long
  undifferentiated list buries the findings that would have changed the design.
- Operator-configurable cap: flexible, but asks for calibration before the
  operator has seen anything, and constitution VI rules out unrequested
  flexibility.

**User's answer:** Top 5, ranked, with omitted count stated (Recommended)

---

### Q14. How should scaffold supply the operator context the Field Guide calls for?

**Branch:** Prompt design

**Recommended answer:** Fixed structural framing, with the literal Field Guide
phrasing retained.
> The source is explicit that the prompt should use the literal words "blindspot
> pass" and "unknown unknowns", and that "giving it context on who you are and
> what you know is usually important". Scaffold can state what it structurally
> knows on every run: the operator has read this roadmap entry and its scope,
> and has not necessarily read the affected code area or the archived artifacts
> of its dependencies. No extra prompt is needed before the interview.

**Alternatives offered:**
- Ask the operator's familiarity first: sharpens what counts as an unknown, but
  front-loads friction onto a step whose job is to improve the interview.
- Generic prompt with no framing: shortest, but drops the ingredient the source
  names as the one that usually matters.

**User's answer:** Fixed structural framing (Recommended)

---

### Q15. Where in the scaffold sequence does the pass run — before the worktree exists, or inside it?

**Branch:** Sequencing

**Recommended answer:** Inside the worktree, immediately before grill-me.
> Step 3 already states that all subsequent commands run from the worktree, and
> the analyst should read the same tree grill-me, autopilot, and the
> implementation will see. This run is the live example: the worktree was
> branched from `origin/main` while the session sat on `brand-001-planning-docs`,
> so a pre-worktree scan would have described code the spec never touches.

**Alternatives offered:**
- Before worktree creation as an early gate: cheapest abort, but scans the wrong
  tree whenever the checkout differs from the branch point — the normal case.
- Inside the worktree but after grill-me: richer target, but findings can no
  longer seed the interview, which is the whole of AC-11.1.

**User's answer:** Inside the worktree, just before grill-me (Recommended)

---

### Q16. Does the operator get a decision point after the findings are presented?

**Branch:** Operator experience

**Recommended answer:** Informational — flow straight into grill-me.
> The interview is itself the decision surface: each finding becomes a question,
> an Open Question, or is dismissed by an answer. A confirmation between two
> interactive steps adds friction without offering a decision the next step does
> not already make better. It also keeps scaffold at exactly one confirmation —
> the chain — which is the seam that separates interactive from autonomous.

**Alternatives offered:**
- Explicit continue/abort: valuable in the worst case, but fires on every run to
  catch a rare one.
- Operator curates findings before seeding: respects expertise, but asks the
  operator to triage unknown unknowns before the interview that would have told
  them which ones matter.

**User's answer:** Informational — flow straight into grill-me (Recommended)

---

### Q17. Should the pass be skippable, the way grill-me deliberately is not?

**Branch:** Scope cuts

**Recommended answer:** Mandatory, no skip flag.
> Mirror the sibling step's hard constraint: grill-me states there is no
> `--no-grill` flag and no skip path, because the step is what makes the
> downstream prompts good enough for autonomous execution. The same argument
> holds here — an operator confident enough to skip the pass is exactly the
> operator whose unknown unknowns are unexamined. One code path to specify,
> test, and document.

**Alternatives offered:**
- Skippable via a flag: respects expertise, but a second code path on both
  platforms and a flag whose correct use is indistinguishable from its
  incorrect use at the moment it is typed.
- Heuristic auto-skip: no flag to misuse, but decides silently that a spec has
  no blind spots, which is a claim nothing in the run can support.

**User's answer:** Mandatory, no skip flag (Recommended)

---

### Q18. If the codebase-analyst dispatch fails or returns nothing usable, what should scaffold do?

**Branch:** Error paths

**Recommended answer:** Fail open, and record the gap visibly.
> Continue into grill-me with nothing seeded, stating plainly in both the
> operator output and the design concept that the pass did not run and why. Two
> house precedents point here: `speckit-pro/agents/uat-runbook-author.md` is
> documented as fail-open and "never blocks PR creation", and grill-me's own
> size estimator is advisory and never reads an exit code as a gate. Recording
> the gap is what separates fail-open from silent skip.

**Alternatives offered:**
- Fail closed: guarantees no spec is scoped without the pass, but makes a
  subagent dispatch a hard dependency of every scaffold run.
- Retry then halt: better recall, but still a hard stop, and it adds retry
  semantics to a prompt-level step with no other machinery.

**User's answer:** Fail open, but record the gap visibly (Recommended)

---

### Q19. Grill-me's output schema has no home for "the pass ran and found N things". Where does that record go without changing the schema?

**Branch:** Artifacts / schema

**Recommended answer:** One line in the doc's existing header blockquote.
> The doc already opens with `> Source: / Date: / Questions asked: / Stop
> reason:`. One more line — findings surfaced, findings omitted, or "did not
> run" with the reason — records it without inventing a section. The findings
> themselves need no new home: those the interview resolved are Q&A entries,
> those it did not are Open Questions, both already defined. Grill-me writes it
> because the seeded scope asks for it, so no output-format file is edited.

**Alternatives offered:**
- New "Blind Spots" section: most legible, but changes grill-me's documented
  output schema — the machinery change Q3 ruled out.
- Operator output only: zero schema pressure, but a later reader cannot tell a
  spec that was scanned and found little from one never scanned at all.

**User's answer:** Header blockquote line, no new section (Recommended)

---

### Q20. What belongs in the closing report's artifact index?

**Branch:** Operator experience

**Recommended answer:** Enumerate what the run actually produced.
> The scaffold-owned artifacts (design concept, workflow file, SPEC-MOC) plus
> whatever the plan stage actually wrote — `spec.md`, `plan.md`, `tasks.md`, and
> the conditional ones: `research.md`, `contracts/`, and the checklist domains
> this spec chose. The set genuinely varies per spec, so a derived index stays
> true; once ART-007 lands, its gallery artifacts and the PR URL join the same
> list without the report changing shape.

**Alternatives offered:**
- Fixed enumerated list: predictable and testable, but prints paths that do not
  exist or omits ones that do.
- Only the files the operator must review: shortest, but drops the two things
  scaffold itself produced and told the operator to review.

**User's answer:** Enumerate what the run actually produced (Recommended)

---

### Q21. ART-011 adds no script — every change is prose in two SKILL.md files. What does verification consist of?

**Branch:** Verification

**Recommended answer:** Layer 1 structure and frontmatter, Codex parity through
`validate-codex-skills` and `validate-codex-parity`, Layer 2 trigger evals
re-run against the reworded description on both platforms, and UAT evidence for
the pass and the chain.
> Exactly what the roadmap's verification line calls for. Both behaviours are
> prompt-level, so nothing new is executable and there is nothing a fixture
> could assert against.

**Alternatives offered:**
- Layer 4 fixture for the report logic: real regression protection, but the
  report is prose a model emits, so testing it means adding a runner helper —
  new machinery and a budget that no longer fits.
- Layer 7 end-to-end integration test: highest confidence, but the run is
  strictly interactive by design, so the test would stub out the step the spec
  exists to improve.

**User's answer:** Layer 1 + Layer 8 parity + Layer 2 evals + UAT (Recommended)

---

## Revision Notes

### 2026-08-12 — Q4's platform-equality premise corrected

Q4 chose an in-session chain and did not split by platform. The **decision
stands**; its unexamined **premise** does not. Q4 assumed both platforms may
attempt the chain under the same condition, and that is factually wrong.

Three shipped facts, each verified during Clarify session 3:

- The Codex scaffold's Hard Constraints say `Do not run the autopilot at the
  end`, and its Output section requires a new task rooted at the worktree while
  forbidding hand-off from the parent checkout.
- The Codex autopilot's Workflow Worktree Binding guard is fail-closed and runs
  before any read or mutation, stopping whenever the supplied workflow path is
  not inside the current checkout.
- A Codex task's workspace root is fixed when the task starts and cannot be
  changed from within the session. Scaffold necessarily begins before the
  worktree exists, so the ordinary Codex session is rooted at the parent
  checkout. Confirmed externally: the CLI exposes no mid-session working-directory
  command, and two open upstream issues describe exactly this gap.

Corrected, superseding Q4's unconditional wording:

1. **Codex** attempts the chain only when the workflow path already resolves
   inside the current checkout — deliberately the same predicate the autopilot
   guard itself applies, so the two can never disagree. Otherwise scaffold asks
   nothing and prints the hand-off command.
2. **Claude** is unchanged. Q4's premise holds there, because Claude's scaffold
   already relocates into the worktree and runs each step from it.
3. A **fourth** permitted platform divergence joins the three FR-022 and SC-011
   already list: whether the chain is attempted at all.

The honest consequence: on Codex the one-command experience is now the exception
rather than the rule. That is a platform capability limit rather than a design
retreat, and the alternative was worse — an unconditional Codex chain either
stops at the guard, making the single confirmation a false promise, or, when a
stale same-named workflow file sits in the parent checkout, runs planning phases
and commits into `main`.

This follows the project's established handling of a corrected premise, matching
the pattern used in `CAR-005-design-concept.md`: amend in place with a dated
note, leave the decision intact.

### 2026-08-12 — Q16's "exactly one confirmation" rationale corrected

Q16's recorded reasoning says the informational-findings choice "keeps scaffold
at exactly one confirmation — the chain — which is the seam that actually
separates interactive from autonomous." The **decision stands**: findings are
informational and flow straight into the interview. The supporting count does
not.

Scaffold already stops for the operator twice before this feature adds anything.
Step 3 asks whether to reuse or recreate an existing worktree, and Step 3.5 waits
for explicit approval before running any documented bootstrap command — and this
repository does document a Worktree Preflight, so that second prompt is live
here, not hypothetical. On the worktree-reuse path, which is the very path the
Codex chain depends on for coverage, Claude reaches the chain having already
asked twice.

Corrected: the confirmation budget this feature is accountable for is **what it
adds** — exactly one, the chain, and only when the chain is attempted. Q16's
argument survives intact under that reading, because the point was never the
absolute count; it was that this feature should not add a second gate between the
findings and the first interview question. It does not.

Downstream: `spec.md` SC-007 and SC-011 scoped to this feature's flow, US3
scenario 5 scoped identically, `contracts/chain-handoff.md` §4 matched, and
`contracts/blind-spot-pass.md` §10 rescoped.

*That last entry was missing from this list when the note was first written, and
the omission is exactly why §10 kept the falsified "exactly one confirmation
outside the interview" wording until the Analyze phase caught it. A revision
note's downstream list is load-bearing: an artifact absent from it does not get
swept. Enumerate every file that repeats the corrected claim, not only the ones
that motivated the correction.*

### Revision note 3 — 2026-08-13 — Q4's in-session chain is not available on either platform

**What Q4 recorded:** the run chains in-session into the autopilot's plan stage
behind one confirmation, so a single invocation carries the operator from
roadmap entry to planned spec.

**What the evidence says.** Scaffold cannot invoke the autopilot. On Claude Code
`speckit-pro/skills/speckit-autopilot/SKILL.md:11` carries
`disable-model-invocation: true`, which the Claude Code skills documentation
defines as "Only you can invoke the skill". It is not incidental: commit
`73dcbcc7` added it deliberately "to close the model-invocation path", and the
flag exists for precisely this class of skill — a seven-phase autonomous run
that commits as it goes is the side effect an operator must trigger themselves.
On Codex CLI no flag forbids it, but no skill in this plugin invokes a sibling
skill from its body, so the mechanism is unverified; shipping an unverified
invocation is worse than printing a command that always works.

**What changed.** Both variants print the hand-off command and the operator runs
it. The confirmation survives and records whether the operator is continuing
now. The check that used to gate the chain now selects the hand-off's form.

**Why this is a premise correction, not a reversal.** Q4 chose in-session
chaining over a printed hand-off on the belief that both were available. One was
not. This follows the same CAR-005 pattern as revision notes 1 and 2: the
decision's *premise* was wrong, so the decision could not stand as recorded.

**Downstream artifacts carrying the superseded claim** — enumerated in full,
which is the lesson revision note 2 recorded:
`speckit-pro/skills/speckit-scaffold-spec/SKILL.md` §9 and §10;
`speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` `## Hard Constraints`
and `## Output`; both variants' frontmatter `description`;
`specs/art-011-scaffold-integration/spec.md` FR-013a, FR-014, FR-015, FR-015a,
FR-015b, FR-017, FR-019, FR-020, SC-007, SC-010, SC-011;
`contracts/chain-handoff.md` §2, §3, §5, §6, §8, §9; `plan.md`; `tasks.md`;
`docs/ai/specs/.process/ART-011-workflow.md`; and the pull request body,
including its `release-note` fence.

**The cost.** Removing the chain makes the whole post-planning apparatus
unreachable — the `## Planning Complete` and `## Planning Incomplete` headings,
the completion test, the resume command and its `--from-phase` derivation, and
the Confidence Gate discriminator. Four checklist domains recorded resolved
findings against those rules. That work is not wasted as a record, but it no
longer ships.

*Lesson: the interview asked whether to chain and how, never whether the
platform permits it. A blind-spot pass over ART-011's own scope — which is the
feature this spec ships — would plausibly have surfaced the flag, since it sits
in the frontmatter of the one skill the whole chain depends on.*

## Decisions recorded without a question

Both were named at the closing checkpoint and accepted with the wrap-up:

- **The chain passes `--stage plan` explicitly.** ART-006 §3 notes that a caller
  omitting the flag reaches the same answer by auto-detection on a freshly
  scaffolded file, so passing it is "explicitness rather than necessity".
- **The closing report is printed, not written to a file.** No new artifact; the
  durable record is the workflow file and the design concept.

## Open Questions

- **What:** The FR-016 chain contract ART-011 builds against is not in the
  working tree. It was deleted when ART-006 was archived and exists only at
  `git show 5e184e33:specs/art-006-autopilot-staging/contracts/scaffold-autopilot-chain.md`.
  **Why deferred:** Recovering or relocating it is an archive-hygiene decision
  outside this slice, and the contract's content is quoted where ART-011 needs
  it (Q4, Q10, Q11).
  **Suggested next step:** During `/speckit-specify`, cite the recovery command
  in the spec so downstream phases can re-read the contract. If the citation
  proves insufficient, raise relocating it under `docs/ai/specs/.process/` as a
  separate hygiene change rather than widening this spec.

- **What:** Exact wording of the reworded scaffold description, and how many
  Layer 2 eval cases it needs on each platform.
  **Why deferred:** Q7 fixed the policy (keep the boundary, add the capability),
  not the text. The case count depends on the final wording.
  **Suggested next step:** Resolve during `/speckit-clarify`; verify by running
  the Layer 2 trigger evals on both platforms before the checklist phase.

- **What:** The literal layout of the closing report — section order, how the
  omitted-findings count and the absent-PR note are phrased.
  **Why deferred:** Q5, Q10, and Q20 fixed placement and content; presentation is
  spec-level detail.
  **Suggested next step:** Settle in `/speckit-specify` as acceptance-criteria
  wording, and confirm through the UAT runbook.

- **What:** `codebase-analyst`'s shipped description frames it for autopilot
  consensus resolution, not for a Field Guide blind-spot pass.
  **Why deferred:** Q2 chose reuse specifically to avoid editing an agent
  definition and restaling the Layer 6 digest chain. The dispatch prompt carries
  the framing instead (Q14).
  **Suggested next step:** Confirm during `/speckit-plan` that a prompt-level
  framing is sufficient. If it is not, the fix is a new spec, not an agent edit
  inside this budget.

- **What:** The declared reviewability budget is now stale in one direction. The
  roadmap says ~4 production files; the interview settled on 2.
  **Why deferred:** The estimator returns `ok` either way (187 LOC, 1 slice), so
  nothing is blocked.
  **Suggested next step:** Re-run `estimate-reviewable-loc` against `plan.md`
  once the Declared File Operations table exists, and amend the roadmap entry if
  the measured figure diverges — the pattern ART-002 and ART-012 both followed.

## Recommended Next Step

Setup has already run; this section is informational. The scaffold continues to
the workflow file, the SPEC-MOC marker, the commits, and the roadmap status
flip, then offers the chain into `/speckit-pro:speckit-autopilot
docs/ai/specs/.process/ART-011-workflow.md --stage plan`.

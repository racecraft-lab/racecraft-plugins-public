Scaffolding a spec and planning it used to be two separate commands, with nothing in between that looked for what the roadmap author had not thought of. This change closes both halves.

```release-note
speckit-scaffold-spec now opens with a read-only blind-spot pass that surfaces unknown unknowns before the interview, seeds them into it, and can continue straight into the autopilot planning stage behind a single confirmation.
```

## What changed

**A blind-spot pass runs before the interview.** Scaffold dispatches the already-shipped read-only `codebase-analyst` to scan the roadmap entry's scope and its dependency chain for hidden coupling, risky surfaces, and unstated assumptions. It returns at most five findings ranked by impact and surprise, and always says how many it set aside. The findings reach the interview through the `scope` argument grill-me already takes, so grill-me itself is untouched.

**The run can continue into planning.** After everything scaffold owns is committed and pushed, one read-only check confirms the workflow file is where the autopilot will look for it, then a single confirmation offers to start the planning stage in the same session. Declining prints the exact command to start it later and rolls nothing back.

**One closing report.** It names the outcome, the draft-PR line, an index of what the run actually produced, and one next step.

## Why

Two capabilities the roadmap called for, from the PRD's acceptance criteria AC-11.1 through AC-11.4. The underlying idea is that unknowns are what force an agent to guess, and accumulated wrong guesses are how long tasks go off course. Finding them costs one read-only scan; finding them later costs a rewrite.

## Non-goals

- **Creating the draft PR** whose URL the report can show. That is ART-007. Until it ships, the report says plainly that there is none rather than fabricating one.
- **Changing grill-me.** No new argument, no output-schema change, no edit to either variant.
- **Any new or edited agent definition.** The analyst is reused exactly as shipped.
- **A separate findings artifact.** Findings live in the design concept only.
- **Widening scaffold's tool grant.** No Grep, Glob, or Bash added.
- **Normalizing the `Key Files` heading** across the eleven roadmaps. The pass degrades instead.
- **A skip flag or a configurable findings cap.** Both were considered and declined.
- **Any new executable machinery.** Every change is prose in two skill files.

## Review order

1. `specs/art-011-scaffold-integration/spec.md` — 31 requirements, 12 success criteria.
2. The two contracts under `contracts/` — these fix the exact strings, so most of the implementation is transcription and can be diffed against them.
3. `speckit-pro/skills/speckit-scaffold-spec/SKILL.md` — the Claude variant.
4. `speckit-pro/codex-skills/speckit-scaffold-spec/SKILL.md` — the Codex mirror.
5. `docs/ai/specs/.process/ART-011-workflow.md` — the run record, including two revision notes where the design changed mid-run.

## Scope budget

Two production files, both skill definitions. Forty files changed: 2 production, 2 test fixtures, 17 spec and doc files, 19 generated. One slice, `one-navigable-PR` by the atomicity classifier, releasable, no warnings.

**Production churn is 1160 changed lines against a scoping estimate of 322**, and both numbers are honest. The 322 was a forward projection from structured signals before any line existed; 1160 is the shipped prose. The repository's own estimator scores this change 0, because it recognises production code only by `src/`, `app/`, `lib/`, `scripts/` prefixes or JavaScript, TypeScript, and SQL suffixes — a plugin shipping Markdown is invisible to it at any size. The gap is flagged rather than smoothed over: 1160 lines is a large read, and a reviewer should know that going in.

## Traceability

Every requirement cites the interview question it came from. The design concept carries two dated revision notes where evidence overturned a decision's premise. The workflow file carries the full consensus log: four rounds, all resolved in the first round.

## Verification

- Full suite **7378/7378**, equal to the recorded baseline. A prose-only change adds no runnable test, and the trigger cases it adds live in fixtures the suite does not execute, so equality is the correct result and proves no regression.
- Layer 1 structural **1447/1447**, including the Codex skill validator and Layer 8 cross-platform parity.
- Both skill descriptions measure exactly **1015 characters** against a hard 1024 cap and hash identically, so cross-platform parity holds by measurement.
- Generated artifacts refreshed; the zero-Bash guard passes.
- Doctor passes. The verification gate passes. The phantom-completion check finds none.
- An independent skill review found nothing at high severity.

## Known gaps

- **The trigger evals have not been run.** They are a live gate outside the default suite, and the Claude runner moves the operator's installed skill directory aside, so no agent should run it. Until it runs, whether the word "planning" — new to scaffold's description and already claimed by the autopilot skill — pulls prompts away from autopilot is untested. Two negative cases per platform are in place to answer it, one stating its precondition and one deliberately short.
- **No UAT runbook.** The skeleton generator is deferred on the installed runner. Both shipped behaviours are prose an agent executes, so UAT is their only observation point.
- **The Codex file has 113 words of headroom** against its 8000-word cap. The next change to it hits the ceiling.
- **Two next-step tables render differently across platforms.** The values are verified identical, so this is presentation rather than behaviour, but it means those two sites cannot be diffed line-for-line against the contract. Left for a follow-up rather than spending the remaining word budget.
- **The chain is Codex-conditional.** A Codex task's workspace root is fixed when the task starts and scaffold runs before the worktree exists, so the ordinary Codex run prints the hand-off instead of chaining. This is a platform limit, not a design retreat; chaining unconditionally would either stop at the autopilot's own guard or, with a stale workflow file in the parent checkout, commit to `main`.

## Rollback

Revert the branch. Both changed files are additive prose at known anchors, nothing is stateful, and no generated artifact depends on the new sections beyond the payload copies that regenerate from source.

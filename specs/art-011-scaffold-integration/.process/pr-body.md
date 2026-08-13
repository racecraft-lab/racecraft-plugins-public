Scaffolding a spec and planning it used to be two separate commands, with nothing in between that looked for what the roadmap author had not thought of. This change closes that gap and makes the seam between the two explicit.

```release-note
speckit-scaffold-spec now opens with a read-only blind-spot pass that surfaces unknown unknowns before the interview, seeds them into it, and closes by handing off the exact command that starts the autopilot planning stage.
```

## What changed

**A blind-spot pass runs before the interview.** Scaffold dispatches the already-shipped read-only `codebase-analyst` to scan the roadmap entry's scope and its dependency chain for hidden coupling, risky surfaces, and unstated assumptions. It returns at most five findings ranked by impact and surprise, and always says how many it set aside. The findings reach the interview through the `scope` argument grill-me already takes, so grill-me itself is untouched.

**The run ends on an explicit hand-off.** After everything scaffold owns is committed and pushed, one read-only check works out whether the operator can run the autopilot from where they are or must re-root first, and selects the command's form accordingly. A single confirmation records whether they are continuing now. Either way the exact command is printed and nothing is rolled back.

**Scaffold does not run the autopilot, and no longer says it will.** The first draft of this PR chained in-session. It could not work: `speckit-pro/skills/speckit-autopilot/SKILL.md:11` carries `disable-model-invocation: true`, which the skills docs define as "Only you can invoke the skill" and which `73dcbcc7` set deliberately to close that path. An independent review caught it before merge. The alternative — dropping the flag — would make a seven-phase autonomous run with auto-commits model-triggerable, which is the exact case the flag exists for. See "Known gaps" for what this cost.

**One closing report.** It names the outcome, the draft-PR line, an index of what the run actually produced, and one next step, under the single heading `## Ready for Planning`.

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
- **Changing `speckit-autopilot`'s frontmatter.** Its `disable-model-invocation` flag stays. Removing it was considered and declined.

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
- Both skill descriptions measure exactly **1013 characters** against a hard 1024 cap and hash identically, so cross-platform parity holds by measurement.
- **Ten shared fixed blocks verified byte-identical** across the two variants — the check block, the confirmation block, the report layout, the hand-off table, the candidate table, and the outcome table among them.
- Generated artifacts refreshed; the zero-Bash guard passes.
- Doctor passes. The verification gate passes. The phantom-completion check finds none.
- An independent skill review found nothing at high severity.

## Known gaps

- **The trigger evals have not been run.** They are a live gate outside the default suite, and the Claude runner moves the operator's installed skill directory aside, so no agent should run it. Until it runs, whether the word "planning" — new to scaffold's description and already claimed by the autopilot skill — pulls prompts away from autopilot is untested. Two negative cases per platform are in place to answer it, one stating its precondition and one deliberately short.
- **No UAT runbook.** The skeleton generator is deferred on the installed runner. Both shipped behaviours are prose an agent executes, so UAT is their only observation point.
- **The in-session chain is gone, and with it a lot of specified behaviour.** Removing it made the whole post-planning apparatus unreachable: the `## Planning Complete` and `## Planning Incomplete` headings, the completion test, the resume command and its `--from-phase` derivation, and the Confidence Gate discriminator. Four checklist domains hold resolved findings against rules that no longer ship. The requirements are marked superseded rather than deleted, so the record stays auditable, but a reviewer reading `spec.md` will meet requirements that describe behaviour this PR does not implement.
- **The confirmation's job is now thin.** Both answers print the same command; the answer selects only how the report frames it. It was kept because it is operator-visible behaviour chosen at interview, but dropping it is a defensible call and a reviewer may want to make it.
- **The Codex file now has 908 words of headroom** against its 8000-word cap, up from 113, because the removed apparatus was large.

## Rollback

Revert the branch. Both changed files are additive prose at known anchors, nothing is stateful, and no generated artifact depends on the new sections beyond the payload copies that regenerate from source.

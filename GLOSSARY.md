# SpecKit Pro

The language of the speckit-pro plugin's workflow: how a SPEC is scaffolded, planned, built and handed to a human for acceptance, on Claude Code and Codex alike. User-facing terms are also explained for plugin users in `docs-site/src/content/docs/glossary.md`.

## Language

**Acceptance run**:
One real SPEC taken end to end by speckit-pro on each host, from the same starting point and the same scaffold answers, then accepted by a human in UAT. It proves the plugin carries real work, where the canary proves it on a fixed fixture.
_Avoid_: pilot run, evidence run, canary

**Answers file**:
A file holding every scaffold interview answer in advance, so scaffold runs without asking. A missing or unknown answer fails scaffold rather than turning into a question.
_Avoid_: pre-answered interview, scaffold script

**Blocked-for-UAT**:
Work a run cannot finish or verify and hands to human review with its reason and evidence, while independent safe work continues. Accepting a documented gap does not make that work complete.
_Avoid_: completed with deferrals, failed run, waived completion

**Canary**:
A fixed small SPEC run end to end, unattended, on both hosts from a clean install: scaffold from an answers file, planning, plan review by a simulated reviewer, and implement. Its green result is what lets a release ship.
_Avoid_: smoke test, integration eval, dogfood run

**Canary receipt**:
The evidence one canary run leaves for one host: the commit, host and plugin versions, the verdict for each variant, and the measures it was judged on. Only a receipt from a canary CI run, scheduled or on demand, can gate a release; a local dogfood receipt never does.
_Avoid_: canary log, test report

**Consensus**:
A second opinion on one planning item from independent analysts. It runs only for security items (all three analysts) and items the executor marks low-confidence (one analyst); every other item takes the executor's recommended answer.
_Avoid_: voting, review, consensus tier

**Decision model**:
A model that returns a typed judgment with probabilities (a yes or no, one option from a fixed list, or a position on a scale) rather than text.
_Avoid_: classifier, LLM judge

**Decisions list**:
The run's record of every judgment it made instead of asking the user: the option chosen, the rejected alternative and the evidence. It never asks for a reply; the reviewer accepts or overturns each entry at review.
_Avoid_: end-of-run request, Decisions for you

**Gate**:
A checkpoint the runner validates at a fixed point in a run, numbered G0 to G7 with G6.5. A gate is a check, never a phase.
_Avoid_: quality gate, phase

**Harm halt**:
The only reason a run ends before a terminal state: the next action could cause damage a later review cannot undo, such as an exposed secret, forged evidence, or a write to the wrong branch. Nothing leaves the machine after it, and a human must clear it before resume.
_Avoid_: integrity failure, hard stop

**Host**:
A coding-agent product that runs the plugin: Claude Code or Codex.

**Host parity**:
The rule that a run gives the same outcomes and the same run experience (prompts, progress block, stop points) on every host. Only one-time host setup may differ. A release needs a green canary on both hosts.
_Avoid_: cross-platform support, Codex support

**Plan approval authority**:
The protected mechanism that establishes a human's final plan approval and its current validity independently of the coding agent. Its review interface records requested corrections and their checked results before final confirmation. Deferred to follow-on work; the health program uses a recorded approval (ADR 0017).
_Avoid_: signing prompt, transcript proof, repository approval flag

**Plan approval record**:
The record of a human's explicit approval of one full planning revision after all planning findings have been fixed and checked. It permits that revision to be built but supplies neither security consent nor proof that implementation work is complete.
_Avoid_: artifact sign-off, planning complete, implementation permission

**Plan review**:
The human interview between planning and implementation that examines the proposed work, closes gaps through revisions, and establishes whether the final planning revision is approved.
_Avoid_: planning pause, implement preflight, artifact delivery

**Plan stage**:
The part of an autopilot run that takes a SPEC from specify through analyze and ends when the review artifacts and the draft PR are ready. The other stages are implement and full.
_Avoid_: planning run, planning phase

**Planning phase**:
One of the six steps inside the plan stage: specify, clarify, plan, checklist, tasks and analyze. Every SPEC runs all six.
_Avoid_: stage, step, gate, quality gate, optional phase

**Progress block**:
The fixed summary of an autopilot run's phases and tasks that the runner renders from autopilot state at every phase transition. It is the only place a run shows its progress.
_Avoid_: task list, todo list, checklist

**Quality-gate thresholds**:
The repository's user-confirmed limits that the complexity, mutation and dependency-rule checks judge changed code against, with the checks it skips or opts into. Only a user's confirmation makes them; an agent never sets them alone.
_Avoid_: gate config, quality settings

**Readiness record**:
Scaffold's snapshot of a project's preparation for a particular host. Autopilot reads that snapshot; new run observations belong to the decisions list and run state.
_Avoid_: preflight approval, readiness certificate

**Retry ladder**:
The fixed sequence of three repair attempts a failing check gets in an autopilot run, each with a stronger agent, before the work it covers is marked blocked. It is the only way a run responds to a failure; a check's count never resets within the run.
_Avoid_: corrective budget, corrective cycle, replan epoch, escalation tier

**Reviewability report**:
An advisory assessment of how much work a SPEC or one of its declared slices asks a human to review. It includes the size evidence and any unresolved uncertainty.
_Avoid_: reviewability block, size gate

**Security block**:
A blocked-for-UAT condition when no safe authorized alternative can satisfy work requiring a security action that cannot proceed. It defers affected work without pausing implement for consent.
_Avoid_: security interrupt during implement, consent retry, permission bypass

**Security interrupt**:
A planning-only pause for explicit consent to one necessary, otherwise permitted security action that has no safe authorized alternative. Refusal defers the affected work while independent safe work continues.
_Avoid_: security approval, permission override, setup question

**Unratified defaults**:
The shipped quality-gate thresholds a run uses when the repository has no valid confirmed thresholds. A run on them never stops for it; the reviewer is told at UAT.
_Avoid_: default gates, fallback config

**Value unit**:
The scope a SPEC commits to: one actor, one observable outcome, one primary surface, and one headline acceptance step a non-engineer can run at UAT. Every SPEC has exactly one; work that outgrows it is a recommended split for a later SPEC, never a reason to stop.
_Avoid_: slice, story, scope budget

# Blocked-for-UAT preserves incomplete work and its evidence for human review

Status: accepted

Implementation status: planning decision; this ticket changes no plugin runtime behavior. The ledger, renderers, resume behavior and host parity described here require implementation and verification.

Decision: [Blocked-for-UAT in the ledger, PR body and UAT runbook](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1023), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

The runner owns one authoritative blocked-work record in execution-control v2 run state. The PR body and UAT runbook render the same record; their authors do not maintain separate lists. A block records incomplete or unverified work, not successful completion. Independent safe work continues until the run reaches its review or UAT boundary.

## Ledger and evidence

The blocked-work record contains typed entries for tasks and gates, linked to their originating check, security item or dependency. Each entry has a stable identity bound to its run and plan revision. Task and gate completion remain distinct from blocked-for-UAT; a blocked task's completion marker stays unchecked.

| Case | Recorded result |
| --- | --- |
| A failing check exhausts its three attempts | Its owning tasks become blocked-for-UAT, linked to the check's fingerprint and attempt evidence (ADR 0004). |
| A task depends on blocked work | Skip it and mark it blocked-for-UAT without an attempt; link to its root blocker. Apply this to transitive dependents. |
| A failing check has no owning task | Mark its gate blocked; do not invent a task owner or mark unrelated completed tasks blocked. |
| Security or consent prevents work | Record the affected work as blocked-for-UAT with its security evidence and any dependent blocks. [ADR 0011](0011-security-interrupt.md) owns classification; [ADR 0014](0014-security-items-during-implement.md) owns skip mechanics. |

Every entry carries:

- The reason and affected task or gate, with the approved-plan reference where applicable.
- The originating check fingerprint, security item or dependency, and links to every applicable root blocker.
- Applicable attempt history, observed outcomes and final failure evidence. A dependency skip or unattempted security item explicitly records no attempt; it never borrows its root's attempt count.
- Retained partial work, what remains unfinished, and which verification is failed, missing or not run.
- What would unblock the work: the repair or missing prerequisite, plus the required verification or consent. This description supplies no authorization.

Keep the original evidence once per cause; dependent entries link to it. Missing or unreadable evidence cannot become a successful result. Record it as unavailable and handle the failing evidence check through the existing retry and stop policies; proven tampering still triggers ADR 0010's harm halt. Public reports use redacted descriptions, repository-relative references and digests; private security evidence follows ADR 0011.

## Partial work and resume

Safe, reviewable partial implementation stays in the review branch, labelled incomplete and unverified with its attributable changes and evidence. Becoming blocked does not itself trigger rollback. Retention never overrides a harm halt, permission boundary or other safety restriction, and retained code alone proves neither completion nor passing verification.

Ordinary resume preserves blocked tasks and gates without redispatching them. It continues independent runnable work and preserves all spent attempts. This applies to dependent blocks as well as root blocks; a later change does not silently reopen either within that run.

Repair requires an explicitly authorized new run linked to the original blocked entries and evidence. The original run's blocks and attempt history remain intact. The repair run has its own attempt history, still follows the fixed ladder and must satisfy the applicable plan-approval and security contracts. A changed plan requires its own valid approval; this decision does not settle how that approval is recorded.

## PR body and UAT runbook

Keep ADR 0010's ordering: the decisions list first, blocked work immediately afterward, and completed work later. The decisions list links to blocked work rather than copying its reasons or evidence. This supersedes the ticket's earlier suggestion that blocked items precede every other section.

Within blocked work, order root causes as follows:

1. Security or consent items.
2. Blocked gates.
3. Exhausted task checks.

Group dependent tasks under their blockers, with stable plan order within each category. A task with several blockers has one detailed entry and links from the other groups; counts never count it twice. Entries carry the evidence above and concrete human review or verification steps. The UAT author may improve step wording but cannot remove a block, change its technical status or claim an unpassed check passed.

The renderers must preserve every canonical blocked entry and its evidence references. Missing entries, changed status, or disagreement between the PR, runbook and runner record are failing checks; an author or renderer failure cannot silently produce a clean handoff.

When independent runnable work is exhausted, an implement handoff with any blocked task or gate says **Ready for UAT with blocked work**. Report completed tasks, blocked tasks and blocked gates separately, with links to the record and runbook. Ready for UAT is a review boundary, not proof that the full plan was built or every check passed. Planning also renders its blocked gates without deciding whether the plan may be approved; that belongs to the plan-approval ticket.

## Human disposition

The reviewer can request repair in a linked new run, accept a documented gap, or reject the handoff. Record that human decision separately from technical status and retain the original evidence. Only actual human input records a disposition; an unanswered review supplies none.

Accepting a gap never marks blocked work complete, changes a failed or unrun check to passed, authorizes a restricted action, or makes a red canary green. A linked repair run needs its own verified completion evidence; it does not rewrite what happened in the original run. Existing waiver and release policies continue to apply.

## Current evidence and required verification

The inspected runtime currently accepts only `complete` and `unfinished` task results and redispatches unfinished work on resume (`speckit-pro/speckit_pro_runner/task_results.py:148`, `:182`, `:305`). PR packets receive deferred items and UAT text as separate inputs (`speckit-pro/speckit_pro_runner/helpers/pr_packet.py:181`), while the UAT skeleton reads the spec and project commands (`speckit-pro/speckit_pro_runner/helpers/uat_skeleton.py:122`). These inspected owners do not provide this shared blocked-work contract. The entire orchestration mapping and a live feature run were not audited.

Implementation must prove, on both hosts:

- Exhausted owning tasks, dependent skips without attempts, ownerless blocked gates, and security blocks preserve distinct evidence and counts.
- Resume never redispatches blocked work or resets spent attempts; an authorized repair run retains its link to the original history.
- Partial code does not satisfy completion evidence, and an ownerless gate failure does not falsely change unrelated task completion.
- PR and runbook render the same entries, links and ordering; duplicate dependencies do not inflate counts, and author failure cannot hide a block.
- A blocked handoff exposes its separate counts, and human acceptance of a gap changes only the recorded disposition.

## Considered options

Separate manually maintained PR and UAT lists were rejected because they drift. Automatic retries on ordinary resume were rejected because they erase the meaning of a terminal block and can evade the ladder. Blanket rollback was rejected because safe partial work remains useful to review and repair. Putting blocked work ahead of the decisions list was rejected to preserve ADR 0010. Treating accepted gaps as completion was rejected because human acceptance cannot supply missing implementation or verification evidence.

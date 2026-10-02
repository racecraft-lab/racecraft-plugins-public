# Implement skips security-blocked work and continues verified independent work

Status: accepted

Implementation status: planning decision; no plugin runtime behavior changes here. Runner enforcement, worker cancellation, blocked-work storage and live host parity require implementation and verification.

Decision: [Security item during implement: skip-and-list mechanics](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1024), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

Implement never asks for security consent. When no safe authorized alternative satisfies the approved requirement, a security action that cannot proceed blocks its owning task immediately. Preserve safe work already done, stop further work on the blocked task, and continue work whose independence and security authority remain verified.

## Admission and immediate skip

Use [ADR 0011](0011-security-interrupt.md)'s existing runner-owned action classification, scope, consent and guard requirements. An already authorized action may proceed under those requirements. Choose a safe authorized alternative when one satisfies the approved requirement, and record that choice in the decisions list; never silently reduce the requirement to avoid a block.

For a necessary action that is forbidden or lacks valid consent, deny dispatch and immediately record its owning task as blocked-for-UAT. Do not first finish additional safe portions of that task. Implement issues no question permit, waits for no consent response, retries no consent request, and invents no repair attempts for an action it never attempted. Plan approval, accepted gaps, endpoint permission alone, and saved readiness observations supply no missing action consent.

Missing or failed guard evidence and incomplete classification evidence retain ADR 0011's treatment: hold protected actions while their failing checks use the retry ladder. Repair may restore evidence or an authorized capability; it may not attempt the restricted action, broaden permissions or bypass a security control. Exhausted checks produce the applicable blocked work. Proven harm still follows [ADR 0010](0010-stop-policy-enforcement.md) immediately; a security block adds no harm-halt reason.

## Affected work and dependencies

The runner derives the affected set from the approved task ownership, completion-unit and dependency evidence. Include every task that requires the blocked action. When tasks share an inseparable test-and-implementation unit and cannot supply valid completion evidence separately, block that unit together. Each affected task retains its own identity and links to the security root; the unit is not an extra task to count.

Skip direct and transitive dependents that require an affected task, unit or unavailable gate result. They become blocked-for-UAT without a new execution attempt and link to every applicable root cause, as in [ADR 0012](0012-blocked-for-uat.md). A shared worker batch, file, phase or agent alone is not evidence of a completion dependency. Unrelated tasks may continue when their approved inputs, completion evidence and security authority remain verified. Existing valid completion evidence for unrelated work is preserved; a blocked ownerless gate does not falsely change completed task status.

If ownership or dependency evidence is missing, malformed or stale, hold work whose independence cannot be verified. Repair the evidence through the retry ladder without dispatching the restricted action or changing the approved plan without fresh approval. After exhaustion, unresolved affected work becomes blocked-for-UAT, with any failing ownerless gate recorded separately. Verified independent work continues throughout. If no remaining work has verifiable independence, all remaining affected work stays held and ultimately blocked; uncertainty never becomes authority to dispatch.

## Work already dispatched

Once a block is known, prevent further affected dispatch and stop affected running work. Cancel affected workers where the host supports it and record the actual cancellation outcome. A worker containing unrelated tasks may be stopped to prevent further affected actions; its still-runnable independent tasks may continue in a clean dispatch after reconciliation. This does not clear any blocked entry or replay any action.

Cancellation is not proof that an in-flight action stopped. Reconcile outcomes using authorized observations; retain known safe partial work and the actual evidence collected. An already dispatched action with an unknown outcome stays explicitly unverified and cannot be replayed automatically. Record real earlier attempts without adding attempts for denied dispatch or dependent skips. Preserve cancellation and outcome uncertainty in the blocked-work evidence; do not claim a side effect was prevented when that cannot be proved.

Independent work continues only while its safety remains enforceable. An actual harm halt stops all dispatch and outward writes under ADR 0010, regardless of the narrower task block. Missing cancellation support or evidence is not a cancellation pass; hold work whose safety or independence cannot be established and handle its failing evidence or capability check through the existing ladder.

## Evidence and human handoff

[ADR 0012](0012-blocked-for-uat.md) remains the sole owner of blocked-work storage, status, resume and rendering. Extend its canonical record with references to the denied action scope, security classification, missing authority or guard/check evidence, affected task/unit/gate, dependency paths to each root, and any dispatch/cancellation/outcome evidence. Retain safe partial work, unfinished requirements, failed or unrun verification, and the exact prerequisite and verification needed for repair. Store cause evidence once, link affected entries, redact public evidence, and never fabricate a denied action's result or attempt.

The decisions list remains first in the PR and UAT runbook; it links to the canonical security block. Blocked work follows immediately, with security/consent roots before other categories and their dependents grouped in stable plan order. Multiple causes share one detailed task entry and do not inflate counts. Keep task completion markers unchecked and report completed tasks, blocked tasks and blocked gates separately. With blocked work, the implement handoff remains **Ready for UAT with blocked work**, not a claim that the full plan was built.

Ordinary resume preserves these blocks. Repair requires the explicitly authorized linked new run and applicable plan/security authority from ADRs 0011 to 0013. Human gap acceptance supplies neither completion evidence nor consent, and it never makes a red canary green. This ticket does not reopen those established storage, resume or display-order decisions.

## Required implementation evidence

Deterministic runner tests and real host-path tests on Claude Code and Codex must prove:

1. A valid authorized action or a safe authorized alternative proceeds without a question; missing consent or a forbidden necessary action causes no restricted dispatch, no consent question, and an immediate owning-task block.
2. No additional work executes within the blocked task. Existing safe partial work remains visibly incomplete; inseparable units and transitive dependents block, while unrelated work in the same batch remains runnable.
3. Dependency chains, diamonds and multiple security roots preserve all root links and count each task once. Ownerless gates stay distinct, and no valid unrelated completion is rewritten as blocked.
4. Missing or stale ownership, dependency, classification or guard evidence cannot authorize dispatch. Its check uses the fixed ladder while verified independent work continues; no repair attempt performs the denied action or changes approval scope.
5. A block discovered after dispatch prevents further affected work. Cancellation records distinguish requested, observed and unavailable outcomes; unknown actions are not replayed, and an actual harm halt stops the whole run.
6. Canonical security evidence, absence of fabricated attempts, retained partial work, persistent resume blocks, rendering order and linked repair-run history satisfy ADR 0012 on both hosts.

These requirements feed [Canary: fixture, variants, receipt, budget, release gate](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1028). They do not resolve its fixture or harness design. A security block alone is not an unregistered stop; missing enforcement or other failed checks cannot be reported green.

## Current evidence and trade-offs

The inspected runtime accepts only `complete` or `unfinished` task results and requires one TDD unit to have a consistent result/evidence set (`speckit-pro/speckit_pro_runner/task_results.py:148`, `:156`). `sidecar_dependencies` reads declared task dependencies (`speckit-pro/speckit_pro_runner/task_execution.py:348`); `make_batches` groups units into worker batches (`:205`), while `batch_waves` co-schedules proven-independent batches (`:249`). These owners provide existing unit/dependency evidence but do not implement the new security-block status and propagation described here. No live worker cancellation or security-block run was tested, and the entire dispatch path was not audited.

The owner chose immediate task blocking over continuing safe parts within it, preserving inseparable completion units over introducing partial unit completion, stopping affected work over cancelling every worker in a wave, and holding uncertain work over immediately blocking all remaining work. These choices preserve honest completion evidence and authority while allowing verified independent progress.

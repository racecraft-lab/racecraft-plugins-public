# The retry ladder replaces corrective budgets and replan epochs

Status: accepted

An autopilot run answers every failure with one mechanism: the retry ladder. A failing check gets three attempts. The current agent tries first. A fresh agent with a consensus diagnosis tries second. The strongest model at max effort, given the full failure history, tries third. Progress earns no extra attempts. When the third attempt fails, the tasks that own the check are marked blocked-for-UAT with the check's evidence, tasks that depend on them are skipped and marked the same way, and the run keeps building everything else. A check with no owning task (a full-suite gate, for example) marks that gate blocked.

Corrective budgets, unit allowances, replan and stage epochs, the frozen-invariant registry, agent-issued approvals, failure-class approvals, and every operator event path (recovery, continuation, the corrective exception and the end-of-run request) are deleted. They stopped runs for operator approval even for one-line fixes, needed two approvals per replan, and turned an empty invariant registry into a hard stop. That broke the promise that implement never stops until the approved plan is built and ready for UAT.

The run stays bounded without budgets. The ladder's unit is a check the runner fingerprints as failing (by command digest), and its count lives for the whole run: a check that passes and later fails again resumes where it stopped. Total attempts are at most three per distinct failing check. The canary's wall clock catches anything that still runs away.

Planning gates climb the same ladder. An exhausted planning gate does not stop the run; it is listed first in the review artifacts and the draft PR, and the plan approval decision covers it.

Metadata-only task rewording survives. The runner proves it scope-neutral against the committed baseline, so it is not a failure path. The ledger moves to execution-control v2; the runner refuses a v1 ledger and asks for a stage restart, with no migration, because the fix vehicle (ADR 0002) keeps real runs out of the plugin until the canary is green.

## Considered Options

- **Keep budgets as the ladder's first rung (today's shape).** Rejected: the ladder only started after a budget ran out and a deferral was recorded, so budget stops stayed the first thing a failure met.
- **Keep the end-of-run request for exhausted units.** Rejected: an operator question at the end is still a stop before ready-for-UAT. Blocked-for-UAT hands the same information to the human at the point they review anyway.
- **One ladder per unit kind (family, increment, gate, class).** Rejected: five kinds with separate rules for one idea. A failing check covers them all.
- **Extra attempts while the failing set shrinks, or five attempts.** Rejected: a deterministic cap matters more than rescuing near-fixes.
- **Reset a check's ladder when it passes, with a run-wide attempt cap.** Rejected: a fix for A that breaks B, then a fix for B that breaks A, would loop until the cap; a count that never resets ends it.
- **Keep the run-wide cap on top-rung attempts.** Rejected: it would block checks that never reached the top rung, for reasons unrelated to them.
- **Stop implement at the first blocked check.** Rejected: independent work would go unbuilt.
- **Keep capped agent replans.** Rejected: a replan during implement changes the plan the user approved.
- **Migrate v1 ledgers.** Rejected: there are no real runs in flight to keep.

## Consequences

- Which model and effort each rung uses on each host is still open, and goes with the ladder-size ticket.
- How blocked-for-UAT is stored in the ledger, the PR body and the UAT runbook is still open.
- The mid-run stops that remain (`checkpoint_required`, ledger integrity errors, harm halts) belong to the stop-policy decision.
- Whether a plan with a blocked planning gate can be approved belongs to the plan approval decision.

# Plan review handoffs

Research date: 2026-10-02. Scope: the single-reviewer, local plan-review prototype. Retrieval: Tavily search, including primary-page content; official publisher pages checked with web tools. This is an interface proposal, not a qualified repair service or implementation authority.

## Recommendation

Give the reviewer two explicit paths after checking their choices:

1. **One or more issues rejected:** end this review and prepare a change-request draft. Explain any withdrawal of an earlier approval before that action. Tell the reviewer to share the draft with the plan author, wait for changes, and review the new version.
2. **Every issue accepted and approval recorded:** open the implementation area, check whether this approval can be used, then separately simulate starting each task. Explain the difference between permission to start and starting work.

Both paths must answer: what happened, what do I do next, who acts next, what information goes with the handoff, and how do I return? No prototype control sends a message, changes a real plan, or runs a real task.

## Primary evidence

| Current primary guidance | Application here |
| --- | --- |
| GOV.UK confirmation guidance calls for a reference, the next steps and timing, relevant destinations, and a record. It acknowledges a research gap when completion is only part of a wider task. [Confirmation pages](https://design-system.service.gov.uk/patterns/confirmation-pages/) | Show a clear result and the next responsible actor. Explain that the demo cannot supply a real delivery time or persistent receipt. Review completion alone is insufficient guidance for the wider planning workflow. |
| GOV.UK check-answers guidance calls for a clear final action, relevant summaries, and a change route for each answer. Edited answers remain populated; continuing returns directly to the summary, unless new questions are required. [Check answers](https://design-system.service.gov.uk/patterns/check-answers/) | Preserve choices when editing. After changing one issue, return to the summary without forcing another unchanged issue through the journey. A changed plan still requires a new review; this recommendation concerns editing a choice for the same plan only. |
| GOV.UK recommends action-specific button wording and avoiding competing primary actions. Serious actions need consequences explained in text, not color alone. [Button](https://design-system.service.gov.uk/components/button/) | Prefer “Prepare change request” over “Continue” at the rejection branch. An action that also withdraws an earlier approval must say so before selection. Label the implementation check for its actual effect. |
| USWDS uses a step indicator for a linear process with separate navigation. It advises a different approach for conditional or nonlinear progression. [Step indicator](https://designsystem.digital.gov/components/step-indicator/) | Keep the existing three review chapters. After the result, show the appropriate next path rather than adding repair and implementation as universal review steps. |
| GOV.UK task-list guidance is for tasks users can complete in their own order, and recommends simplifying before adopting it. It rules out this component for a required sequence. [Task list](https://design-system.service.gov.uk/components/task-list/) | Do not turn the prototype’s two dependent start actions into a freely ordered checklist. Show precise readiness and start status beside each action. |
| GitHub distinguishes general feedback, approval, and requesting changes. A review summary accompanies the selected outcome. Requesting changes is informational unless configured protection makes it enforceable. [Reviewing proposed changes](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request) | Use specific feedback and a clear outcome, but do not inherit GitHub permission or merge behavior as plan-approval authority. A local draft is neither a submitted GitHub review nor proof that repair has started. |

These sources support the interaction principles. They do not prescribe this prototype’s approval, withdrawal, or repair rules. The selected paths below are design inferences constrained by its existing model.

## Selected rejection path

The review summary shows every issue and choice, with separate change actions. If any issue is rejected, approval stays blocked. Show the rejected issues together with a short explanation: “You cannot approve this plan while any issue is rejected.”

The selected terminal action uses the existing `CANCEL` behavior. This ends the unfinished review and withdraws any currently active earlier approval. This consequence must be visible before selection:

- With no active earlier approval: **End review and prepare changes**. Explain that this review ends without a new approval.
- With an active earlier approval: **Withdraw approval and prepare changes**. Explain that the earlier approval will no longer permit implementation.

This is intentional withdrawal, not an implicit effect of rejecting an issue, visiting a draft screen, or submitting feedback. The action does not submit feedback. The existing snapshot and choices remain available after `CANCEL`; model history remains visible.

The next screen is **Change request draft**. Include the reviewed version, rejected issue identifiers and descriptions, all review choices, and a field for the reviewer’s requested change for each rejected issue. A useful prompt is **What must change?** Keep the exact issue identifiers in the draft even when the interface uses simpler display names.

Suggested result and next-step copy:

> This review has ended. No change request has been sent. Share this draft with the plan author. After the author changes the plan, review the new version.

Also show the precise earlier-approval result when applicable. Avoid “Changes requested”, “Sent”, “Queued”, “Repair started”, or “Waiting for the agent” without a real acknowledged handoff. A text-selection or copy action can help the reviewer share the draft; its success must be observable. Say that local draft text is lost on reload if the implementation keeps it only in memory.

A valid alternative is **Prepare change request** as navigation alone: it leaves the review open and an earlier approval active. That path requires an explicit explanation of this continued authority. The terminal path was selected to give the reviewer a clear stop and an intentional withdrawal option without adding model policy.

## Selected approval-to-implementation path

After final approval, show **Approval recorded** with the reviewed version and record reference. Explain that the accepted issues remain unresolved, permission for sensitive actions is separate, and work has not started.

Offer **Open implementation**. This changes the area only. In that area:

1. **Check approval for implementation** maps to `ADMIT`. It checks the current approval and exact inputs. A passing result means the demo can proceed; it starts no task.
2. **Simulate starting task 1** maps to its existing start action. Show **Start recorded in demo**, never “Completed”. No real task runs.
3. **Simulate starting task 2** becomes available only when the model permits it. Its existing dependency is task 1’s start record, not task 1’s completion. Explain that limitation beside the action.

If permission checks fail, name the relevant problem and recovery route. Plan changes require a fresh review. Missing trust or status requires restoring that evidence; changing areas or accepting an issue cannot repair it. Preserve the original failure detail in technical information.

## Future real handoff contract

The real service still needs a chosen recipient and transport, explicit dispatch authority, a stable request identifier, confirmed delivery, author acknowledgement, repair status, and a route back to review. A repair request should identify the reviewed version, rejected issues, reviewer instructions, and originating review. The returned plan must identify its new version and changes; previous acceptance must not be silently copied.

The implementation service needs a separately authorized invocation, current approval checks at use, precise task start and completion states, retry rules, and failure recovery. A delivery acknowledgement, permission check, task-start acknowledgement, and completion result are different facts. The current demo cannot establish these production contracts through copy or navigation.

These fields and states are recommendations from the domain constraints, not requirements imposed by the cited design systems. Choosing a transport or executing a real repair is outside this research task.

## Verification goals

- Reject one issue, check the summary, and prepare the draft. No approval, message, repair, or task is created. The requested withdrawal has the existing `CANCEL` effect, including an older active record.
- Verify every rejected issue appears in the draft, exact identifiers remain, and notes render as text. Editing a decision returns to the summary with other choices retained.
- Confirm with all issues accepted. Opening implementation changes no approval or task state. A passing implementation check creates no task-start record.
- Record task 1’s simulated start and then task 2’s. Neither status implies completion or real execution. Duplicate starts remain blocked.
- Change the plan before implementation use. The old approval remains historical; a new review must collect new choices before confirmation.
- Ask the intended reviewer, without coaching, to explain who acts next, whether a request was sent, whether work started, and what they must do after plan changes. A correct agent walkthrough cannot establish reviewer comprehension.

The approval model and canonical artifact branding must remain unchanged. This report alone does not verify the proposed interface, user comprehension, signing, or security.

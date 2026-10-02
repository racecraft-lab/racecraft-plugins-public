# Plan review information architecture

Date: 2026-10-02. Status: implemented prototype proposal; human evaluation pending.

The operator's later evaluation found that the simulation lacked meaningful repairs and that Implementation and Scenarios were unclear. The [operator domain model](plan-review-domain-model.md) now supersedes this revision's unresolved-finding acceptance journey and peer-area navigation. The observations below describe the earlier checkpoint, not acceptance of that design.

This proposal responds to the reviewer's difficulty understanding what to do in the prototype. It applies the [primary-source research](../research/plan-review-information-architecture.md) to the [interactive review prototype](plan-approval-authority-prototype.html), preserving the existing artifact library's canonical brand and the approval model.

## Actor and goal

The actor is the human plan reviewer. The goal is to read the proposed work, decide whether to accept each remaining finding, and explicitly confirm the reviewed version. Review ends with a receipt. Starting implementation is a separate action in a separate area.

The opening screen states the role, goal and completion condition before showing one primary action: **Start review**. The simulation notice remains visible.

## Structure

| Area or screen | Information the actor needs | Main action |
| --- | --- | --- |
| Review: opening | Role, goal, steps and consequence | Start review |
| 1. Read the plan | Frozen version, scope, proposed tasks, evidence and effective settings; full bundle inspectable in place | Review findings |
| 2. Decide findings | One named finding at a time, relevant evidence, technical condition, acceptance/rejection consequences, previous choice and decision count | Explicit individual Accept or Reject; Next finding / Back |
| 3. Check and confirm | Exact reviewed bundle and both dispositions, what confirmation means, routes to change decisions and any blocking reason | Confirm review, explicitly |
| Review complete | Modeled receipt, reviewed version and finding decisions; clear statement that implementation has not started | Optional Open implementation; Withdraw approval |
| Implementation | Separate actor goal, approval prerequisite, current status and ordered task simulation | Start implementation, then each task separately |
| Scenarios | Optional guided cases, intentionally invalid actions, fault controls and model diagnostics; warning that cases change fixture state | Select a case or explore a fault |
| About | Setup, instructions, design question and qualification limitations | Read supporting information |

The three-chapter indicator describes progress; it does not replace Back/Continue navigation. Each active screen states the current task and next action. Hidden steps are excluded from keyboard navigation. Full state remains inspectable in the Scenarios area.

## Domain constraints

- Navigation changes presentation only. It does not prove reading or supply approval.
- Starting review uses the existing frozen snapshot operation. Required material stays inside the review context rather than being filed as optional help.
- Every finding requires its own choice, with no default acceptance. Acceptance leaves its technical condition unresolved. Rejection prevents confirmation and offers a route to change the decision or cancel.
- Final confirmation remains a distinct model action. The interface derives eligibility from pure reducer previews rather than adding another approval policy.
- Completion does not invoke implementation. Opening Implementation only changes areas; admission and task actions remain explicit.
- Canceling an unfinished review and withdrawing an issued approval have different labels and explanations.
- Changed, withdrawn, stale or unverifiable inputs retain the model's refusal behavior. Recovery is explained without silently clearing history or weakening checks.
- Canonical BRAND-KIT, GALLERY-HEAD and the pure approval-model script remain unchanged. Native signing and security qualification are outside this IA revision.

## Verification plan

Walk through the actor's valid review in the Browser, inspect the full review material in context, revisit a finding, reject a finding, and check explicit confirmation and separate implementation. Also verify cancellation/withdrawal, changed-plan and revoked-status refusal, navigation without state loss, keyboard focus, light/dark themes and a narrow viewport. Re-run existing ephemeral syntax, reducer and DOM checks, including all nine guided cases and 35 free actions.

The Browser walkthrough observed the focused review journey, full material in context, rejection and changed choices, Back preservation, explicit confirmation, separate implementation admission and ordered task actions, withdrawal retaining its receipt with one renewal action, cancellation with and without an earlier receipt, and changed-plan recovery requiring new choices for R2. Light and dark themes rendered, and focus moved to the current chapter heading on navigation. Source review and ephemeral DOM checks also exercised authority/evidence blockers, all nine guided cases and 35 actions. The three scripts parse, and the pure model and canonical brand/head blocks are byte-identical to the prior checkpoint. Browser observations use the default viewport; a narrow-screen usability evaluation remains unrun.

These checks establish observed prototype behavior. The proposed structure still needs the intended reviewer's uncoached walkthrough; no human comprehension improvement or security qualification is claimed from agent checks.

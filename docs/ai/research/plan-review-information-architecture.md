# Plan review information architecture research

Research date: 2026-10-02. Scope: a single human reviewer using the synthetic plan-approval prototype. This recommends an interface structure; it does not qualify signing, consent capture, enforcement, or authority.

## Recommendation

Replace the simultaneous four-stage dashboard with a focused review journey. State the reviewer’s role and goal first, show one current task with its relevant evidence and consequence, and give an explicit next action. Keep implementation as a separate handoff after review completion. Keep scenario controls, setup, and diagnostics outside the review journey.

This is a synthesis of current primary guidance, not a claim that one universally best or newest IA exists. Several recommendations are longstanding and remain in current design systems. The proposed structure still needs evaluation with the intended reviewer.

## Evidence to design

| Primary evidence | Application to this prototype |
| --- | --- |
| GOV.UK recommends starting with one question per page, a heading, Back, and Continue. It cautions against large progress indicators that combine all questions with navigation. [Question pages](https://design-system.service.gov.uk/patterns/question-pages/) | Show one meaningful review task at a time. Each finding remains a distinct decision. Do not put every future action on the initial screen. |
| USWDS reserves a step indicator for three or more linear high-level chapters, with separate navigation, an explicit heading, and current-step text. It advises against it for nonlinear or highly conditional flows. [Step indicator](https://designsystem.digital.gov/components/step-indicator/) | Use a compact three-chapter indicator: Read plan → Decide findings → Confirm review. Findings can have their own count inside chapter two. Use Back/Continue controls rather than clickable progress segments. |
| GOV.UK limits task-list pages to longer transactions that may span several sessions and says to simplify first. [Complete multiple tasks](https://design-system.service.gov.uk/patterns/complete-multiple-tasks/) | Prefer a short guided journey over a dashboard of task cards. Reconsider a task list only if future real reviews become large or resumable. |
| NN/g says progressive disclosure works only when the initial view contains the important and frequent features, and the route to secondary material is clear. [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) | Move fault controls and technical state into clearly named secondary areas. Keep the actual plan, risk, finding evidence, and decision consequences in the review view. |
| USWDS recommends small meaningful chunks, contextual help, and visible progress; it warns against hiding critical explanations behind navigation away from the task. [Progress easily](https://designsystem.digital.gov/patterns/complete-a-complex-form/progress-easily/) | Explain what each acceptance means beside its controls. Use inline expandable supporting detail where necessary; do not require a trip to a guide to understand an approval. |
| NN/g recommends recognition over recall by making needed information and available functions visible. [Recognition and recall](https://www.nngroup.com/articles/recognition-and-recall/) | Restate the plan identity, scope, finding, and prior choice where needed. The reviewer should not remember technical labels from another panel. |
| NN/g identifies vague labels and competing calls to action as sources of confusion. [Common IA mistakes](https://www.nngroup.com/articles/3-ia-mistakes/) | Use concrete labels such as “Read plan,” “Review findings,” “Confirm review,” “Test scenarios,” and “Technical details.” Avoid action labels such as “Invoke” or “Admission” in the reviewer journey. |
| GOV.UK places a check-answers screen immediately before confirmation, with relevant sections, meaningful action labels, and routes to change earlier answers. [Check answers](https://design-system.service.gov.uk/patterns/check-answers/) | Before final confirmation, show the reviewed plan, each finding’s disposition, scope, and consequence. Allow revisiting decisions while preserving the prototype’s existing invalidation rules. |
| GOV.UK confirmation guidance calls for a clear completion result and what happens next; it acknowledges research gaps when a transaction is part of a wider task. [Confirmation pages](https://design-system.service.gov.uk/patterns/confirmation-pages/) | End review with a receipt: review recorded; implementation has not started. Offer a separately labeled implementation simulation rather than advancing automatically into dispatch. |
| WCAG 2.2 requires headings and labels to describe purpose, meaningful focus order, and programmatically identifiable status messages where applicable. W3C’s explanatory documents are informative, not the normative standard. [Headings and labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels.html), [Focus order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html), [Status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), [WCAG 2.2](https://www.w3.org/TR/WCAG22/) | Give every screen a descriptive heading; keep hidden steps out of keyboard navigation; manage focus sensibly on screen changes; announce decision results and blocking status without relying on color. Test the resulting interface rather than inheriting another system’s compliance claim. |

## Proposed structure

1. **Review plan** — default area. A short opening explains: “You are the reviewer. Read this plan, decide each remaining finding, then confirm your review. Implementation starts separately.” Keep the simulation notice visible without overwhelming the task.
   - **Read plan:** show purpose, scope, work proposed, excluded work, and relevant evidence. Full snapshot details remain available in context. Finish with a clearly labeled continue action.
   - **Decide findings:** show one finding at a time: plain-language issue, evidence, proposed disposition, consequences of accepting or rejecting, and an explicit individual choice. No default acceptance. Show how many decisions remain.
   - **Confirm review:** summarize the plan and decisions, provide meaningful change actions, and explain the final confirmation’s consequence. Show a contextual reason if confirmation is blocked.
   - **Review recorded:** show the modeled receipt and separate next action. A clearly labeled implementation simulation opens a distinct surface with its own actor, scope, and checks.
2. **Test scenarios** — optional guided cases and fault exploration. Explicitly warn before resetting/changing an active review. Returning to review retains current state when no scenario mutation occurred.
3. **About and technical details** — setup, limitations, authority model, full state, history, and diagnostic controls. This is not a prerequisite for finding the default task.

These are organization and labeling recommendations, not a requirement to install GOV.UK or USWDS components. Preserve the existing speckit-pro artifact library’s canonical brand, theme, typography, spacing, and focus styles.

The guided sequence uses **staged disclosure**; moving optional tools behind secondary navigation uses **progressive disclosure**. NN/g distinguishes these and warns that staged flows are less useful when people must repeatedly alternate between interdependent steps. Keep the frozen plan and evidence inspectable alongside finding decisions and the final check to address that limitation. [Progressive and staged disclosure](https://www.nngroup.com/articles/progressive-disclosure/#staged-disclosure-one-step-at-a-time)

## Evaluation and limits

The existing source exposes all four stage headings and many controls at once. That inspection supports the redesign hypothesis; it does not prove the cause of every comprehension problem.

Use a brief walkthrough with the intended reviewer. Before coaching, ask them to identify their role, goal, current task, available decision, consequence, and next action. Then ask them to complete review, change one decision, find the full scope, and explain whether implementation has started. Record wrong turns and misunderstood labels. These are proposed acceptance tasks, not measured results.

For secondary navigation, test finding a scenario, the approval limitation, and the technical record without naming the destination category in the task. NN/g distinguishes tree testing of hierarchy/labels from full usability testing, which also assesses layout and interaction. An agent walkthrough or a single reviewer session cannot establish population-wide success rates. [Tree testing](https://www.nngroup.com/articles/tree-testing/)

The research does not justify hiding material evidence, merging independent finding decisions, treating navigation as approval, auto-starting implementation, or claiming real human consent from a simulation. Domain approval semantics must remain unchanged while the presentation improves.

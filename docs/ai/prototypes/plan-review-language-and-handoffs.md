# Review language and next steps

## Question and evidence

Can a reviewer understand each choice and move from the review to changes or implementation without learning the internal approval terminology?

The human requested simpler prose based on ASD-STE100 and research into both next-action paths. The team used Tavily to retrieve the complete official Issue 9 and primary interface guidance. See [simplified-language research](../research/plan-review-simplified-language.md) and [review handoff research](../research/plan-review-handoffs.md). An independent actor audit checked the display against the existing model.

This is a proposed interface for human evaluation, not a qualified approval authority or a shipped implementation. Human comprehension remains unmeasured.

## Selected language approach

Use STE-inspired writing and plain-language interface guidance. Aim for at most 20 words in instructions and 25 in explanations. Give one action per instruction. State a necessary condition before the action. Name the actor and explain the result beside each consequential control.

These are editorial targets, not formal STE conformance. The standard has dictionary, grammar, domain-vocabulary and counting requirements beyond short sentences. Its dictionary does not generally approve several necessary product terms. Replacing those words mechanically would change the meaning of consent.

Use the following display vocabulary consistently:

| Internal idea | Reviewer wording |
| --- | --- |
| Synthetic simulation or fixture | Demo or sample plan |
| Frozen planning bundle and review epoch | Plan version and this review |
| Residual finding | Issue; explain whether a check has not passed or a plan assumption needs proof |
| Finding disposition | Your choice |
| Canonical record or receipt | Review record |
| Admission | Check whether work can start |
| Dispatch receipt | Task-start record |

Preserve exact file contents, identifiers, model messages and diagnostic values in optional technical details. A readable summary does not replace the material being reviewed. Unknown failures remain visible. A short explanation must not change a rule or imply that a check passed.

## Review paths

The reviewer reads one plan version, chooses separately for both issues, then checks those choices. Editing a choice from the summary should return to the summary. Navigation never supplies consent.

### An issue is rejected

Give the reviewer an explicit end-review action that prepares a local change-request draft. With an earlier active approval, the action must explicitly say that it withdraws that approval. Explain the effect before the action.

This path uses the existing `CANCEL` transition. A rejected choice alone leaves an earlier active approval usable in the model. The selected terminal path ends the review and removes that possibility through an explicit withdrawal. It does not treat cancellation as message submission. Merely opening a draft while leaving the review active would be a different design and would need to show that the earlier approval remains usable.

The draft identifies the reviewed version, both choices, rejected issues and their supporting references. State that no request was sent and the plan has not changed. The next actor is the person or coding agent who wrote the plan. The reviewer gives that actor the draft and asks for changes. After the plan changes, the reviewer starts a new review and makes new choices.

The demo can show a changed sample plan through its existing `CHANGE_PLAN` action. This changes the sample version only; it neither remediates the issues nor proves that changes are correct.

### Both issues are accepted

Keep final confirmation explicit. It creates a demo review record for the exact reviewed material and choices. Accepting an issue does not fix it. Confirmation does not start implementation or supply separate permission for protected actions.

After confirmation, offer navigation to the separate implementation area. That area first checks whether the approval permits work (`ADMIT`). This check starts no task. The person starting work then explicitly tests each task start (`DISPATCH`). Task 2 requires a recorded start for task 1, not proof that task 1 completed. The demo runs no real task.

## Verification goals

- Preserve the pure approval model, exact synthetic inputs and canonical artifact branding byte for byte.
- Exercise each choice, editing, explicit confirmation and refused confirmation.
- Exercise a change-request draft with and without an earlier approval; confirm its explicit withdrawal blocks implementation admission.
- Show a revised sample plan, then require a new review and new choices.
- Exercise separate implementation admission and ordered task starts without claiming completion.
- Keep raw refusal reasons and exact review material inspectable; check that hostile sample text remains inert.

Observed verification will be recorded in the [prototype evidence](plan-approval-authority-evidence.md). No sentence-length score, agent audit or scripted journey establishes human comprehension or security qualification.

# Plan review: operator domain model

Status: repair cycle and simpler remediation choices implemented and locally checked. Human acceptance is pending.

## Goal and confirmed decisions

The operator wants a plan with its issues corrected and checked so implementation can begin.

- The interface constructs a handoff prompt. The operator copies it into their current Claude Code or Codex session. The agent presents its revised plan for a new review.
- Every finding must be fixed and checked before approval. An acceptance click cannot close a finding.
- Approval and the later human start of implementation remain separate actions.
- Implementation uses another copyable handoff prompt. The interface does not send messages, launch a session or start tasks.
- Repairs are limited to requested fixes and necessary dependent task, contract and check updates. Every resulting change is explained.
- The revised review compares each original issue with its correction and check result. The reviewer approves the whole revised plan once; separate confirmation of every correction is not required.

The copy-and-paste instruction supersedes the earlier answers that suggested direct agent return or an implementation launch from this interface. Those answers described the desired outcome; the operator subsequently clarified the transport.

The second decision is stricter than [ADR 0013](../../adr/0013-plan-approval-record.md), which permits explicit acceptance of remaining gaps. This prototype proposal records the new human requirement; the accepted ADR and shipped plugin have not been changed. Their policy must be reconciled before implementation.

## Simple issue-to-handoff refinement

The operator requires the main experience to make each issue, its impact and its possible remedies clear immediately. Two compact issue cards are the working surface. Each contains a short problem statement, a short impact statement, a recommended remedy, a meaningful alternative and **Write my own instructions**. Plan context and exact source remain optional details.

The operator explicitly chooses a remedy for each issue. A recommendation is not selected automatically. One **Build handoff prompt** action validates the choices, retains them for editing and constructs the exact unsent request. Missing choices and empty custom instructions produce direct errors without losing other answers. Choosing a radio option neither navigates nor changes technical issue status.

| Issue | Recommended remedy | Alternative | What both preserve |
| --- | --- | --- | --- |
| The two review documents can disagree | Feed both documents the same snapshot of the shared task list. | Generate one immutable report from that shared list and feed both documents the report. | One runner-owned authority, the same source revision, all entries/status/evidence/order/counts and no independent edits. |
| Resume would erase stopped-work history | Keep history and prepare an inert linked repair-request draft at handoff. | Keep history and prepare that draft only when the reviewer requests repair. | Original blocks, attempts and evidence; no automatic retry; a new linked repair run still needs explicit authorization. |

The second issue's alternatives change when repair instructions are prepared. They do not offer permission to discard history. The first issue's report is a derived view, not another authoritative task list. These alternatives are design proposals consistent with ADR 0012, not additional accepted repository decisions.

The request stores the selected remedy and its exact instructions. The example revised plan, affected tasks/contracts and planning report must distinguish the built-in options. A custom request remains **Not checked** until an actual response and matching checks address it. Matching a custom sentence to a catalog phrase cannot turn it into verified evidence. A copied prompt cannot supply protected plan approval or start implementation.

Native radio groups, associated labels, simple conditional text areas, actionable errors, visible focus and large clickable labels support keyboard and assistive-technology use. Browser verification checks these behaviors and narrow layout. It does not establish complete WCAG or screen-reader conformance.

## Terms and actors

Use the repository's [glossary](../../../GLOSSARY.md) for plan review, plan approval authority and plan approval record. The following objects make the repair journey explicit.

| Object | Meaning for the operator |
| --- | --- |
| Plan revision | One exact version of the proposed work, tasks, settings and supporting material. |
| Finding | A specific problem in that revision, with its impact and supporting information. |
| Remedy selection | The fix the operator asks for: a recommended option, another offered option or their own instructions. Choosing a remedy does not fix or check the issue. |
| Change request | The selected corrections the reviewer asks the planning agent to make, tied to the reviewed revision and findings. |
| Handoff prompt | Text the operator copies into their coding-agent session to request a planning repair or separately start implementation. Preparing or copying it sends nothing. |
| Planning repair | Work that corrects the plan and reconciles affected tasks, contracts, artifacts and other planning outputs. |
| Check report | Results for the checks affected by the repair, including checks that failed or could not run. A reference or a version label is not a result. |
| Revised review | The corrected plan, a comparison with the requested changes and the new check results. |
| Implementation run | A separately started run that builds the approved plan. Starting a task does not prove that it is complete. |

| Actor | Responsibility |
| --- | --- |
| Human reviewer | Understand the proposed work, request corrections, assess their evidence and explicitly approve the final revision. |
| Planning agent | Repair the plan, reconcile its dependent outputs, rerun affected planning checks and return the revised material. |
| Person starting implementation | Copy the implementation handoff into the coding-agent session to explicitly start a separate run after approval. This can be the reviewer acting at a later step. |
| Approval authority and runner | Validate approval and the exact inputs before work starts and before each task. These checks are not manual reviewer tasks. |

## Operator journey

1. Read each issue's short explanation and impact. Open the proposed plan or source details when needed.
2. Choose the recommended fix, another offered fix or write your own instructions for each issue.
3. Build and copy the change-request prompt into the planning agent's session. Edit the choices before copying when needed.
4. Return to the revised review material. Inspect each requested change beside the agent's correction and affected check results.
5. Request further changes if any finding remains unresolved or its fix cannot be checked.
6. Explicitly approve the final reviewed revision when all findings are fixed and checked.
7. Prepare and copy the separate implementation handoff into the coding-agent session. The runner performs admission and per-task enforcement.

The prototype must label all simulated agent work and check results. An explicit demo control loads the example revised plan. It must not pretend that a prompt was sent or that a real agent replied. A revised version number alone proves no correction. Merely displaying a fix proves neither human approval nor protected signing.

Planning corrections are checked against the requested change and repository contract. Implementation tests for code that has not yet been written remain future work. Simulated planning results must not be presented as observed code tests or security qualification.

## Boundary with prototype tools

Fault injection, raw model actions, manual task dispatch and safeguard test cases belong in optional prototype tools. They are not steps in the operator's plan-review journey. Opening a test case must disclose that it resets the sample state.

Setup, instructions and security qualification information remain separate from the review experience. Essential plan material and check evidence stay available within review. The existing artifact library remains the visual source of truth.

## Repository-grounded example candidates

These examples use real repository decisions. Their flawed first plans, agent repairs and displayed results would be explicitly simulated, not observed repository defects or passing tests.

| Example | Repository grounding | Proposed plan findings |
| --- | --- | --- |
| Ask before saving project check settings | [ADR 0007](../../adr/0007-quality-gates-scaffold-proposes-autopilot-defaults.md) requires human confirmation before saving proposed thresholds and disclosure of unconfirmed defaults. | The initial plan saves settings automatically; it also omits the effect of whole-file checks on existing code. A repair adds confirmation, decline behavior and the missing explanation. |
| Keep unfinished tasks visible in review documents and on resume | [ADR 0012](../../adr/0012-blocked-for-uat.md) requires one authoritative blocked-work record, unchecked blocked tasks and preserved attempts on resume. | The initial plan creates independent unfinished-task lists for the PR and acceptance runbook; it also resets blocked tasks on resume. A repair uses the same record and preserves blocks and attempts. |

The second example offers two concrete planning defects that can both be corrected, matching the operator's new requirement. The first combines a required correction with a disclosure of an unavoidable tradeoff.

The second example is selected for the revised prototype. The initial plan, two defects, repair output and check reports remain fictional examples grounded in ADR 0012.

## Interface research applied

The [GOV.UK summary-list component](https://design-system.service.gov.uk/components/summary-list/) supports clear label/value presentation of plan metadata. The [check-answers pattern](https://design-system.service.gov.uk/patterns/check-answers/) supports explicit final submission, relevant sections and returning directly to the summary after an edit. The [confirmation-page pattern](https://design-system.service.gov.uk/patterns/confirmation-pages/) supports explaining the next action after a transaction.

Those sources inform presentation. They do not decide this repository's readiness policy or prove operator comprehension. Tavily retrieved the guidance during this refinement.

## Interview record

| Question | Operator decision |
| --- | --- |
| What is the goal? | Correct and check the plan's issues so implementation can begin. |
| What happens after a change request? | Return it to the planning agent, then review the revision. |
| What makes the plan ready? | Every finding is fixed and checked before approval. |
| Where does implementation start? | The interface prepares a prompt the operator copies into Claude Code or Codex. This later correction replaces direct launch. |
| What can a repair change? | Requested fixes and necessary dependent outputs only, with every resulting change explained. |
| How are corrections approved? | Compare the issues, corrections and check results; approve the revised plan once. |

## Verification and remaining decisions

The revised HTML implements this model with two fictional plan defects grounded in ADR 0012, changed revised inputs and explicit simulated planning results. The main form immediately presents two issues and their choices. Browser checks cover native radio navigation, custom-text focus and retention, actionable errors, read-only prompts, exact clipboard copies, alternative-specific revisions, further choices and refusal of unchecked custom requests. Both themes and a narrow layout were inspected. The model/DOM smoke covers all four built-in combinations, nine safeguard cases and 45 controls. Independent audit verifies pending requests block approval and task use, omitted remedies cannot reuse earlier checks, retained choices are not silently replaced and superseded runners remain blocked. These observations provide local interface evidence for human evaluation. They do not qualify protected signing, full accessibility conformance or the shipped runner.

Human acceptance of the review experience is pending. Reconcile the all-findings-fixed requirement with ADR 0013 before shipped implementation. Real revised-package import, actual agent responses/check evidence, protected review/signing/enrollment and current authority enforcement remain separate implementation and qualification work.

This document is a proposal. It supplies no real agent messaging, approval authority, signing, enrollment or implementation execution.

---
name: speckit-plan-review
<!-- host:claude: Claude reads a trigger-phrase description and Claude-only frontmatter keys -->
description: "Use only when the user explicitly asks to review a finished SpecKit plan with you before implementation: walk through the decisions list, every blocked planning gate, every low-confidence finding and the user's own change requests, one at a time, then build one copyable prompt that asks the planning agent for a repair, or, once every finding is fixed and checked, record your approval of the final revision and prepare a separate implement prompt. Triggers on: plan review, review the plan, review the planning findings, walk me through the plan, build the repair prompt, withdraw an instruction, approve the plan, prepare the implement prompt. Sends nothing and starts no planning or implementation. Do NOT use to run planning or implement (use speckit-autopilot), to scaffold a spec (use speckit-scaffold-spec), or to read project status (use speckit-status)."
argument-hint: "[feature directory or SPEC-ID]"
user-invocable: true
disable-model-invocation: true
allowed-tools: Read Glob Grep
license: MIT
<!-- /host -->
<!-- host:codex: Codex keeps its own selection description -->
description: >
  Review a finished SpecKit plan with the user before implementation.
  Walks the decisions list, blocked planning gates, low-confidence
  findings and the user's own requests, one at a time, then builds one
  copyable repair prompt. Once every finding is fixed and checked, records
  the user's approval of the final revision and prepares a separate implement
  prompt. Sends nothing and starts no planning or implementation. Invoke only
  when the user asks for a plan review.
<!-- /host -->
---

# SpecKit Plan Review

An interview between planning and implement. The user decides what to fix. You
guide the interview and call runner helpers. The runner owns every rule about
revisions and findings.

This skill builds a repair prompt, or an implement prompt, for the user to copy. It sends nothing and
starts no planning, repair or implementation. It records an approval only after the user explicitly
approves the final revision with every finding fixed and checked (step 5). Its writes are the user's
active requests, which the runner records in the feature's `planning-findings.json`, and that one approval.

## Capability discovery & grounding

<!-- host:claude: Claude resolves plugin files through CLAUDE_PLUGIN_ROOT -->
Before recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `${CLAUDE_PLUGIN_ROOT}/skills/speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->
<!-- host:codex: Codex has no plugin-root variable, so it links relative to this skill -->
Before recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `../speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `../speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.
<!-- /host -->

## Installed Runtime Contract

Resolve `<plugin-root>` per [Installed runner transport](../speckit-autopilot/references/installed-runtime.md).
Send one JSON request per runner call on stdin and read one JSON reply. Add no shell step. Runner helpers follow the session's permissions; if one is denied, say so and stop that step.

## Invocation

```text
<!-- host:claude: Claude names skills with a slash -->
/speckit-pro:speckit-plan-review <feature-dir>
<!-- /host -->
<!-- host:codex: Codex names skills with a dollar sign -->
$speckit-pro:speckit-plan-review <feature-dir>
<!-- /host -->
```

## What to Do

Run this even when planning reported no findings. A clean plan still gets a
review. Finish the interview in step 2 before deciding whether a repair prompt is needed.

### 1. Gather the material

Use the feature directory the user names, or its workflow file when given.
Make these runner calls, all `mode=read_only`:

- `helper_id=planning-approval operation=planning-approval`, `action=manifest`, with
  `feature_dir` and `workflow_file`: the revision under review (`manifest_digest`).
- `helper_id=decisions-list operation=decisions-list`, with `workflow_file`: the decisions list.

Read the feature's `planning-findings.json` and the workflow file for the blocked
planning gates and the strict low-confidence findings. Keep each id the file lists
(`confidence-<criterion>` for a strict finding): the approval record needs those exact
ids. Give a short id only to a finding the file does not list. If any source is
missing, say which and what it would have shown.

### 2. Explain, then ask

Open with the revision, the count of findings and the decisions list in plain words.
Walk through each decision, one question at a time: give its impact, the recommended choice,
one real alternative and room for a custom instruction, and check the user understands it.
A change the user wants becomes their own request. Then ask for the user's own change requests,
even when there are no reported findings. Wait for those answers.
Then take the findings one at a time: every blocked gate, every strict low-confidence
finding, and each request the user raises themselves (give those the id `USER-1`, `USER-2`).
For each finding:

1. Say what the problem is and its impact, in short sentences.
2. Offer a recommended fix, one real alternative and a custom instruction.
3. Ask one question. Recommend one answer first. Wait for the answer.

Record each answer as a request: an `id` (`R1`, `R2`), the `finding`, a `kind`
(`recommended`, `alternative` or `custom`) and the exact `instruction`. A
choice, an acceptance of risk or silence closes nothing. Every finding needs a
request.

After those answers, if there are no findings or requests, say that no repair
prompt is needed and go to step 5 for the final approval.

### 3. Withdraw an instruction

If the user changes their mind about a custom instruction, show its exact text,
request id and finding. Withdraw it only after they confirm that text. Never
delete a request: keep the full list and add the withdrawal. The finding stays
required, so ask for a replacement request.

### 4. Build the repair prompt

Call `helper_id=plan-review-prompt operation=plan-review-prompt mode=apply` with
`feature_dir`, `workflow_file`, `reviewed_revision` (the `manifest_digest` captured in step 1),
`findings` (`id`, `summary`), `requests` (all of them, in order,
withdrawn ones included) and `withdrawals` (`request`, `finding`, `instruction`; an empty list when none).
The runner builds the prompt and, in the same call, records each active request under its finding
in `planning-findings.json`. A refusal writes nothing. `mode=dry_run` checks the same inputs and
writes nothing.

If the runner says the reviewed revision changed, the plan moved during the review:
restart at step 1 with the new revision and repeat the interview. For any other refusal,
read its message, fix the named field with the user and call again.
On success, show `data.prompt` in a fenced text block and tell the user:

- Copy it into their current Claude Code or Codex session. Preparing it sent nothing.
- The planning agent repairs the plan and returns a revised bundle for a new review.
- To change a request later, run this skill again with the full request list. The runner keeps
  every recorded request unless that list withdraws it, and only a custom request can be withdrawn.

### 5. Approve the final revision

Reach this step when the planning agent has returned a repaired revision, or when the plan had no findings
and the interview in step 2 asked for no repair. Step 1 captured that revision's `manifest_digest`.

1. Put each finding side by side: the request the user made, the correction that came back, and its
   planning check result with the evidence reference. Use `planning-findings.json` for the ids and requests.
   The correction and the passing check for every finding must exist for this exact revision.
2. If any finding lacks a correction or a passing check, name it and stop. Offer a new repair prompt
   (step 4). Do not ask for approval. Accepting a risk, a chosen remedy and silence close no finding.
3. Otherwise ask once: does the user approve this whole final revision, named by its `manifest_digest`?
   One explicit yes covers the whole revision. Silence, a generic "looks good", elapsed time, your own
   assessment and an earlier approval of another revision are not approval; ask again, or stop.
4. On an explicit yes, build the `approval` object and its confirmation file as
   [Recorded planning approval helper](../speckit-autopilot/references/planning-approval.md) describes,
   in the order it gives. The confirmation holds `decision=approve`, the `manifest_digest`, the `approver`
   the user named and the decision `time` with a timezone. Keep the user's words out of it.
5. Call `helper_id=planning-approval operation=planning-approval`, `action=record`, with the `approval`
   object, first with `mode=dry_run`, then with `mode=apply`. The runner refuses a missing, failed or
   mismatched check, a missing or generic confirmation and a revision that moved. Read the message
   and fix the named field with the user; a refusal writes nothing.
6. On success, show `data.implement_prompt.prompt` in a fenced text block and tell the user:
   - The approval is recorded, not protected. It grants no security consent.
   - Copy the prompt into their current Claude Code or Codex session when they want to implement. Preparing
     it sent nothing and started nothing.
   - Any later change to the planning inputs needs a new review and approval.

### 6. Stop

Do not run the repair. Do not start planning or implementation. Tell the user the plan is approved only after
the runner records the approval in step 5. A plan with an open finding or a changed revision is not approved.

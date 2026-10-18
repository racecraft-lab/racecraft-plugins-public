---
name: speckit-plan-review
description: >
  Review a finished SpecKit plan with the user before implementation.
  Walks the decisions list, blocked planning gates, low-confidence
  findings and the user's own requests, one at a time, then builds one
  copyable repair prompt. Sends nothing and starts no planning or
  implementation. Invoke only when the user asks for a plan review.
---

# SpecKit Plan Review

An interview between planning and implement. The user decides what to fix. You
guide the interview and call runner helpers. The runner owns every rule about
revisions and findings.

This skill builds a repair prompt for the user to copy. It sends nothing and
starts no planning, repair or implementation. It records no approval.

## Capability discovery & grounding

Before recommending, enumerate the tools and skills your session actually exposes — do not assume a fixed set; the user may have installed anything — and select the best fit per `../speckit-autopilot/references/capability-discovery.md`. Ground every external fact you assert in a real tool, skill, or file result per `../speckit-autopilot/references/grounding.md`, and abstain when nothing grounds it.

## Installed Runtime Contract

Resolve `<plugin-root>` per [Installed runner transport](../speckit-autopilot/references/installed-runtime.md).
Send one JSON request per runner call on stdin and read one JSON reply. Add no shell step. Runner helpers follow the session's permissions; if one is denied, say so and stop that step.

## Invocation

```text
$speckit-pro:speckit-plan-review <feature-dir>
```

## What to Do

Run this even when planning reported no findings. A clean plan still gets a
review. With no findings, say so and stop at the end of step 2.

### 1. Gather the material

Use the feature directory the user names, or its workflow file when given.
Make these runner calls, all `mode=read_only`:

- `helper_id=planning-approval operation=planning-approval`, `action=manifest`, with
  `feature_dir` and `workflow_file`: the revision under review (`manifest_digest`).
- `helper_id=decisions-list operation=decisions-list`, with `workflow_file`: the decisions list.

Read the feature's `planning-findings.json` and the workflow file for the blocked
planning gates and the strict low-confidence findings. Name each finding with a
short id. If any source is missing, say which and what it would have shown.

### 2. Explain, then ask

Open with the revision, the count of findings and the decisions list in plain words.
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

### 3. Withdraw an instruction

If the user changes their mind about a custom instruction, show its exact text,
request id and finding. Withdraw it only after they confirm that text. Never
delete a request: keep the full list and add the withdrawal. The finding stays
required, so ask for a replacement request.

### 4. Build the repair prompt

Call `helper_id=plan-review-prompt operation=plan-review-prompt mode=read_only` with
`feature_dir`, `workflow_file`, `findings` (`id`, `summary`), `requests` (all of them, in order,
withdrawn ones included) and `withdrawals` (`request`, `finding`, `instruction`; an empty list when none).

If the runner refuses, read its message, fix the named field with the user and call again.
On success, show `data.prompt` in a fenced text block and tell the user:

- Copy it into their current Claude Code or Codex session. Preparing it sent nothing.
- The planning agent repairs the plan and returns a revised bundle for a new review.
- To change a request later, run this skill again with the full request list.

### 5. Stop

Do not run the repair. Do not start planning or implementation. Do not tell the user
the plan is approved: this skill records no approval, and a revised plan needs a new review.

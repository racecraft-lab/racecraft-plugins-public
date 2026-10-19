# Plan review request recording

## What changed

`plan-review-prompt` now runs in `dry_run` and `apply` as well as `read_only`.
`apply` records each finding's active request instructions, in review order, in
the feature's `planning-findings.json`, in the same call that builds the repair
prompt. Before this, nothing filled the request lists that planning left empty,
so `planning-approval record` could never approve a plan whose strict findings
were fixed and checked.

The inventory publisher is `planning_approval.update_inventory`. It captures
bytes and file identity in one snapshot and publishes through the checked write
that `finish-plan-stage` already uses. `requests_recorded` is the pure rule:
named findings take the review's active instructions, unnamed findings keep
their entries, and a recorded request leaves only when the review withdraws it.
The inventory is a planning input, so `apply` moves the manifest digest. The
prompt and `data.revision` name the digest after the write; a repeat `apply`
with that digest changes nothing.

## Known limits

Reachability reasons follow each item.

- **Low: a built-in (recommended or alternative) request cannot be changed once
  recorded.** The runner refuses a rerun that omits it, and only a custom
  request can be withdrawn (ADR 0013). This is the stated contract: a built-in
  remedy cannot silently withdraw an earlier one. A reviewer who needs it gone
  edits the committed inventory by hand; that moves the manifest digest and
  forces a fresh review.
- **Low: a mistyped finding id the reviewer raised is added to the inventory.**
  A withdrawn custom request leaves the finding listed with no request, so
  approval stays refused until it is fixed by hand. Fail-closed.
- **Low: withdrawn requests are not kept in the inventory.** The inventory holds
  active instructions only, because `planning-approval` compares it with the
  approval record. The withdrawal history stays in the `history` field of the
  reply and in the review transcript.
- **Low: instructions that differ only in surrounding whitespace count as
  different requests.** The exact text is the request (ADR 0013). Both need a
  correction at approval, so nothing is admitted early.
- **Info: `writes_state` is true for every `apply`, including a repeat that
  changes nothing.** `planning-approval` reports it the same way.
- **Info: the revision check and the inventory snapshot are separate reads.**
  An edit between them cannot lose data, because the merge runs on the
  snapshot the write is checked against. It can only let a call pass a revision
  that moved a moment earlier; the approval's own digest check still binds the
  final revision.
- **Info: a linked or unreadable inventory is refused earlier, by the manifest
  call that supplies `reviewed_revision`,** so the write path never sees it.
- Linux VM tests do not provide macOS coverage; the orchestrator runs that
  before merging. No live plan-review interview was run: the skill text was
  checked against the runner's documented request schema.

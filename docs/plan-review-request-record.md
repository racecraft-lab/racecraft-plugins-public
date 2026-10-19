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
The inventory is a planning input, so `apply` can move the current manifest
digest. The prompt's `Reviewed revision` and `data.revision` always retain the
exact digest the reviewer supplied and the helper validated before recording
requests. Recording requests does not review the resulting bundle. A repeat
call must supply that bundle's current digest; final approval still requires
reviewing the repaired bundle and its checks.

The helper never reads planning inputs after inventory publication to assign a
reviewed label. Concurrent edits to feature files, workflows, project inputs,
declared formal inputs, or the inventory therefore cannot acquire that label.
Removal, rename, link replacement, and unreadability after publication cannot
produce the former post-write manifest refusal either. The same runner ships
to both hosts. `PlanReviewConcurrentRevisionTest` covers both publication
windows and content edits, replacement, rename, symlink, hard link, removal,
unreadability, and added files for each input category; inventory mutations
exercise the post-publication window (its checked publisher owns the earlier
window). Every case runs with an empty inventory that must be written and an
already-recorded inventory that needs no write, so the inventory change cannot
mask a mutation that fails to reach the planning manifest. Added formal inputs
are declared in the catalog; denied reads are injected as well as chmodded to
keep that failure deterministic for privileged test users.

## Known limits

Reachability reasons follow each item.

- **Low: request withdrawal provenance is recorded as text only.** Although
  the supplied request list permits withdrawal only for `custom` entries, the
  inventory has no original kind or request id. A caller can retype a recorded
  recommended or alternative request as custom, or omit its original id and
  withdraw a new custom alias carrying the same text, then replace it. This
  requires control of the helper request and inventory; the normal skill asks
  for confirmation of custom withdrawals. It grants no extra authority to
  untrusted content and does not create an approval. This remains an accepted
  limit of this PR's inventory format.
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
  snapshot the write is checked against. The returned reviewed digest still
  names only the input revision that passed validation, even if the current
  bundle has moved; the approval's own digest check binds the final revision.
- **Info: a linked or unreadable inventory is refused earlier, by the manifest
  call that supplies `reviewed_revision`,** so the write path never sees it.
- Linux VM tests do not provide macOS coverage; the orchestrator runs that
  before merging. No live plan-review interview was run: the skill text was
  checked against the runner's documented request schema.

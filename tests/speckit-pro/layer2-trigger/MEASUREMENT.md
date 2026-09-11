# Trigger measurement prerequisite

The measurement prerequisite for [issue #573](https://github.com/racecraft-lab/racecraft-plugins-public/issues/573)
is **not qualified**. The current patch repairs reproduced parser and process
defects and makes diagnostic trial outcomes replayable. It does not authorize
corpus pruning or a qualifying baseline/candidate matrix.

The pinned-interface assessment is in
[`measurement-capabilities.json`](measurement-capabilities.json). Its status is
blocked. Recheck versions and complete the missing observations before freezing
a measurement implementation. A passing diagnostic case does not clear that
gate.

## What the repair establishes

- Claude validates the result identity, order, and successful completion of
  every observed Skill invocation, including siblings and the no-op skill. It
  rejects undeclared tool activity and conflicting reported model identities.
- Codex rejects failed, declined, unfinished, or unsuccessfully exited completed
  command items, and events outside the single completed turn.
- Both hosts use bounded process supervision, preserve exact partial streams,
  and check the original owned process group before starting another trial.
  An exited leader with lingering descendants is invalid even if cleanup later
  succeeds. Processes outside that group are outside the proof.
- Both hosts persist one typed trial record before continuing. Invalid evidence
  stops the loop immediately. Valid behavioral failures still allow the runner
  to finish its cases; a later matrix driver must apply the comparison stopping
  rule at a completed host/skill arm pair.

## Diagnostic evidence format

Each new evidence directory contains exact `case-NNN-trial-NN.jsonl` and
`.stderr.log` files, plus a versioned `.trial.json` record with their paths and
SHA-256 hashes. Files are created exclusively. Existing evidence directories and
report files are never reused.

The `trigger-trial/v1` record contains stable logical case identity, case/trial
ordinals, the exact submitted query and its hash, expected label, parser
observations, and typed supervision observations. `provider_exit_code` is the
observed child return code, or null if unobserved. The legacy `exit_code` alias
contains the same value; the query helper's timeout sentinel is not an observed
provider exit. Timeouts and interruptions have separate fields.

`stream_valid` records the parser outcome. `trial_valid` is the conjunction of
the recorded process, stream, model, selection-output, and cleanup checks for
the declared diagnostic observation scope. The legacy `valid` field is exactly
the same canonical value. This patch has **not** established the missing native,
exclusive-selection, configuration, or retry requirements listed in the
capability record. `qualification_eligible` therefore remains false for all
records and reports; the current schema must not be treated as qualified matrix
evidence.

The runner report includes each retained record and its own path/hash. Counts
come from canonically valid trials. `status: not_run` has null counts and no
trial observations. An incomplete or invalid case has a null trigger rate,
explicit executed and unexecuted trial counts, and cannot pass. `summary.complete`
requires every case to have all requested valid trials; it says nothing about
the separate measurement qualification gate.

`trial-stop.json` identifies the first invalid trial. Supervision exceptions
also retain a `.failure.json` diagnostic. `isolation-stop.json` preserves the
Codex isolation diagnostic when applicable. No report is synthesized for a
failure before provider launch; missing reports block comparison.

`arm-cleanup.json` is written after workspace removal and records the actual
runner exit, cleanup error, and whether the workspace is absent. The earlier
report is preliminary until this receipt is checked. Runner exits are:

| Exit | Meaning |
| --- | --- |
| 0 | Diagnostic cases passed; workspace cleanup still requires its receipt |
| 1 | Behavioral failure, invalid evidence, or preflight/runtime error; inspect the complete report and receipt to distinguish them |
| 2 | Workspace cleanup or cleanup-receipt retention failed |
| 128 + signal | Interrupted runner, unless workspace cleanup failure superseded it |

The future comparator must independently validate raw hashes, containment,
record identities, parser replay, typed execution checks, summary agreement,
runner exit, and the cleanup receipt. It must reject missing evidence and a
blocked capability record. Replaying historical JSONL cannot reconstruct an
unrecorded process exit or repair an old report.

## Remaining qualification blockers

Claude's documented `UserPromptExpansion` event observes direct slash-command
expansion, separately from model-initiated Skill calls. Its observer and prompt
binding have not been demonstrated in this isolated runner. Restricted mode
still accepts managed and explicit settings; the effective configuration must
be frozen and validated. Reported retries are rejected, but the absence of a
retry event does not establish zero invisible transport retries.
([Direct invocation](https://code.claude.com/docs/en/hooks#userpromptexpansion),
[restricted mode](https://code.claude.com/docs/en/cli-reference))

The pinned Codex 0.153.3 public JSON schema exposes command and message events,
but no skill-activation event or complete selected-skill set. Its thread/turn
start records do not report backend model identity. An exact output marker is
a proxy, and a file read alone does not establish activation. Consequently the
current observer cannot qualify target-plus-sibling ambiguity or native
selection. App-server notifications and internal rollout fields cannot be
silently substituted for this interface.
([Pinned event schema](https://raw.githubusercontent.com/openai/codex/rust-v0.153.3/codex-rs/exec/src/exec_events.rs))

The process tests use synthetic streams and local Python children. No provider
inference was used to validate this patch. Corpus dispositions, independent
pruning review, the strict comparator, frozen arm provenance, and a full live
matrix remain subsequent gated work. Original corpora and PR #572 evidence are
unchanged by this prerequisite.

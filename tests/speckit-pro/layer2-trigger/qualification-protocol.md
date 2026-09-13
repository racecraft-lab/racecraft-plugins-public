# Trigger qualification and scoped feedback

The provider-free planner and comparator do not establish native qualification.
An accepted PR-core result covers only its declared selection. Unknown or global
impact expands the selection to the full corpus. Keep historical evidence intact;
missing parser context makes an old run diagnostic, not retrospectively eligible.

## Frozen coverage

The reviewed inventory accounts for all 438 original occurrences and retains all
14 protected identities. Its revised 23 host/skill corpora contain 217 cases:
105 Claude and 112 Codex. Three trials in each of two behavior arms require 1,302
native launches, a 50.46% reduction from 2,628. The minimum reduction target is
met; the 200-case stretch target is not. This is launch arithmetic, not a measured
token, billing, latency, or behavior result.

Semantic review approved the inventory with SHA-256
`0dfbf5670912e7806c7b588394c7ffd25d1ab8dc01acca1a9263f9df2151bdf1`.
Any edit invalidates that approval. Do not prune cases after observing outcomes.

## Controlled comparison

For the closure experiment, both arms use the same final runner, parser, corpus,
inventory, fixtures, and skill catalog. Only the `no-speckit-skill` description
changes. The baseline description is recovered from the parent of public commit
`6ef717ed` (PR #572); the candidate is that commit's approved description, still
present in baseline commit `42f4afe5bd2a319f81ea4b28799ec13bfa8e6107`.
The exact strings and source paths are in `controlled-descriptions.json`.
This trigger baseline differs from the **autopilot performance** baseline, which
uses the unchanged installed harness at the latter full commit.

Freeze a `trigger-experiment/v1` only after integration and artifact generation.
Review its exact roster, raw inventory digest, parser/catalog/fixture identities,
model and CLI versions, trial settings, scope, and controlled description digests.
The manifest must include positive integer `trial_timeout_seconds`. The campaign
call's `--timeout` must equal that value; both native runners retain it in report
metadata and independent replay rejects a missing or different value. Changing
the timeout requires a newly reviewed manifest and invalidates prior concurrency
qualification. Historical reports without this evidence remain diagnostic.
Do not substitute a current runner with the historical runner: that would vary
more than the approved behavior difference. Do not treat placeholder pins or an
approval-shaped JSON object as a user's authorization.

Preserve the existing host model-evidence policy. Codex's exact requested model
and CLI argument binding may qualify under its existing `requested-only` policy
when the native stream omits a resolved model identifier; report the resolved
identifier as null, not as an observed backend identity. Compare resolved model
identifiers when present, reject contradictions and cross-arm policy changes,
and retain the existing Claude resolved-model requirements. The official
[Codex non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode)
does not promise a model identifier on every JSONL event. This limitation is not
permission to substitute a model or relax other trial-eligibility checks.

## Launch authorization and isolation

Every campaign needs separate user approval of its exact manifest and launch
budget. Reserve identities before launching; unknown outcomes consume budget.
There are no automatic retries. Recover owned processes and artifacts before
requesting subsequent authorization. Keep credential material outside evidence.

First run the 48-launch pilot: four reviewed cases per host, three trials, one
fixed behavior arm, under serial and two-worker schedules. Keep trials within a
case sequential. Both schedules must have valid complete evidence, unchanged
behavior, disjoint workspace/config/temp/output ownership, and confirmed cleanup.
Two workers qualify only when elapsed time is at least 25% below serial. Retain
all raw start/end observations; never report missing or invalid work as faster.
Full campaigns default to serial until this pilot qualifies a global ceiling of
two workers. More workers require another approved experiment.

The pilot is **additional**: 48 pilot launches plus 1,302 full-matrix launches
equals 1,350 planned launches, before any separately approved campaign. A failed
pilot does not authorize a replacement run or a larger budget.

## Evidence and acceptance

Retain immutable per-trial stdout, execution metadata, parser replay context,
Codex witness bodies, cleanup evidence, and artifact digests. Publish the evidence
index only after those artifacts are complete. Independently replay the native
parsers and join by stable case/trial identities, never report order.

Report completeness, execution validity, candidate acceptance, regressions, and
qualification separately. Positive target hits falling from 3 to 2 and negative
hits increasing from 0 to 1 are regressions even if Boolean grades pass. Positive
0 to 1 remains below the unchanged 0.5 acceptance threshold. Comparator exits are
0 accepted, 1 valid behavioral failure, and 2 invalid or incomplete evidence.

Artifact hashes establish byte integrity, not independent provider authorship.
Keep the trusted orchestrator's actual execution and approval observations with
the campaign record; worker assertions or copied messages are not that authority.

Do not close the public issue until all eight criteria and a complete eligible
dual-host matrix are satisfied. The broader performance program additionally
requires matched completed autopilot benchmarks, under-two-hour full workflows,
and at least 50% lower per-host median runtime. PR feedback under 15 minutes is
measured only for the declared feedback scope. Human UAT is pending until done.

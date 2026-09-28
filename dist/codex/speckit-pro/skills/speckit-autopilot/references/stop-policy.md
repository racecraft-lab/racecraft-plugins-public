# Autopilot Stop Policy

One contract for when an autopilot run may involve a human. Claude and Codex
autopilot both load it. The runner owns the closed set of stop reasons in
`speckit_pro_runner/stop_policy.py`. Guidance names a reason with
the marker `stop_reason:` followed by the id, and never invents one. A parity test enforces both.

## The rule

Once a run starts, agents own it until the PR stack is ready for human review.
Agents solve problems by spawning more agents, not by asking a human.

A run involves a human for two reasons only:

1. The next step needs authority agents do not have.
2. A problem has failed every escalation tier.

A run also halts at once for a harm halt, described below.

Attended and unattended runs behave the same. Autopilot never pauses to ask. A
present user may interrupt or steer at any time.

## Defer, do not halt

A stop condition does not halt the run. Park the blocked unit, keep running
every independent unit, and put every human item into one end-of-run request.
The ledger `defer` disposition is that park.

The run halts at once only for a harm halt: continuing could compound harm.

## Escalation tiers

A problem is exhausted only after all three tiers fail.

1. The current agent's repair loop, within its allowance.
2. A fresh agent with a different approach, guided by a consensus diagnosis.
3. The strongest model at max effort, given the full failure history.

Tier 3 has a per-run cap, default 3 uses, recorded in the ledger and enforced by
the runner. Past the cap, the problem defers straight to the end-of-run list.

## Scope questions

When the spec and roadmap do not settle a product-scope question, answer it by
consensus with the narrowest option that satisfies the spec. Record it as an
assumption and list it under "Decisions for you". Defer only a choice that would
add scope or change public behavior beyond the spec.

## Run-start grants

Tool installs and network egress are granted once, in the run-start
authorization. They never stop a run midway.

## End of run

Mark the stack ready for review with a "Decisions for you" section listing each
deferred item and its evidence. Keep it draft only while a required gate is red.
Deferred decisions and human UAT never hold a PR in draft. Never merge.

The `--stage plan` boundary stays: a plan-stage run stops after the plan for
human review.

## Stop reasons

Each reason has one class.

| Reason | Class | Meaning |
| ------ | ----- | ------- |
| `stop_reason:merge` | authority | Merging a PR. |
| `stop_reason:publish` | authority | Publishing a release or package. |
| `stop_reason:protected_push` | authority | Pushing to a protected branch. |
| `stop_reason:secrets` | authority | Reading, creating, or changing a secret. |
| `stop_reason:destructive_action` | authority | A destructive or irreversible action. |
| `stop_reason:human_uat` | authority | Human user acceptance testing. |
| `stop_reason:scope_changing_pr_split` | authority | Splitting a PR in a way that changes scope. |
| `stop_reason:boundary_file_edit` | authority | Editing a file the boundary rules protect. |
| `stop_reason:veto_bypass` | authority | Bypassing a veto. |
| `stop_reason:reopen_closed_pr` | authority | Reopening a closed PR. |
| `stop_reason:all_tiers_failed` | exhausted | All three escalation tiers failed. |
| `stop_reason:tier3_cap_reached` | exhausted | The per-run tier 3 cap is spent. |
| `stop_reason:tampering_or_forged_evidence` | harm_halt | Tampering or forged evidence. |
| `stop_reason:secret_exposure` | harm_halt | A secret was exposed. |
| `stop_reason:integrity_failure` | harm_halt | An integrity failure. |

Authority and exhausted reasons defer. Harm halt reasons halt the run.

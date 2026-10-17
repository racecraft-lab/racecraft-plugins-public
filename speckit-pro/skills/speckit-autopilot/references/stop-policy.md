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

A run also halts at once for a harm halt, described below. The runner decides when
a run may end (`may_end` in `stop_policy.py`): only in a run end below, or on a harm halt.

Attended and unattended runs behave the same. Autopilot never pauses to ask. A
present user may interrupt or steer at any time.

## Defer, do not halt

A stop condition does not halt the run. Park the blocked unit, keep running
every independent unit, and put every human item into one end-of-run request.
The ledger `defer` disposition is that park.

The run halts at once only for a harm halt: continuing could compound harm.

## Harm halts

A harm halt fires when the next action could cause damage a later review cannot
undo. On a harm halt the runner stops all dispatch: no commit, push, PR edit or
publish follows the trigger, because a PR edit could spread a leaked secret. It
writes a local halt record (reason, redacted evidence, last safe state) and
prints it. Resume refuses until a human clears the record with the `harm-halt`
helper (`action` `clear`). On resume, run `harm-halt` in `read_only` mode first;
a `halted` answer ends the run with the recorded reason's marker.

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

The run settles, before Phase 1, everything its start-up inventory can know:

- Codex: the standing policy classes, the egress of each gate and declared
  pre-PR command, an external workflow root, and the private record write. Each
  is probed. A missing standing policy is the single up-front ask, and the run
  starts on the operator's reply.
- Claude Code: the session's permission settings. One no-op runner request and
  one `git status` run first. If either prompts or is denied, the run prints the
  exact allow rule and stops once, before any phase work.

Any run-start probe that prompts or is denied is settled in that one ask.
Nothing that inventory could have known is discovered mid-run. Bypassing a veto
stays human authority: `stop_reason:veto_bypass`.

## End of run

The unpushed-commit Stop hook checks settled publication work. Runner
`publication_pending` defers that check while plan rows are pending/in progress
or ledger dispatches are reserved, running, or unknown. Continue collecting
workers; the plan terminal and completed-work checkpoints own their pushes.
Missing, unreadable, malformed, or unbound ledger evidence cannot establish
unsettled dispatches, so the hook still checks Git unless a valid pending plan
row defers publication. Invalid plan rows do not prevent that check.

Mark the stack ready for review with a "Decisions for you" section listing each
deferred item and its evidence. Keep it draft only while a required gate is red.
Deferred decisions and human UAT never hold a PR in draft. Never merge.

A default planning run ends at the plan boundary: artifacts and the draft PR are
ready for review (`planning_ready_for_review`, marker `stop_reason:plan_stage_boundary`).
Opt-in `--strict` also stays: below the confidence threshold it stops before Phase 7
(`stop_reason:strict_confidence_opt_in`). `--strict` does not apply to a default run.

## Run ends

| State | Kind | Meaning |
| ----- | ---- | ------- |
| `planning_ready_for_review` | terminal | Planning artifacts and the draft PR are ready for review. |
| `ready_for_uat` | terminal | Implementation is done and only human UAT remains. |
| `security_interrupt` | interrupt | A permitted security question is open (ADR 0011). |

## Stop reasons

Each reason has one class. When a stop ends the run, print exactly one marker for that reason,
copied verbatim from the Reason column, as the last line of the final message, on
its own line. Do not repeat it in the report or append text after it. A deferred
item does not end the run and prints no marker.

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
| `stop_reason:tool_unavailable` | authority | `gh` is absent or not authenticated. Installing or signing in is a run-start grant. |
| `stop_reason:ambiguous_pr_record` | authority | The recorded PR is missing, or several open PRs match the branch. Choosing the right PR is a human call. |
| `stop_reason:plan_stage_boundary` | authority | A `--stage plan` run stops after the plan. |
| `stop_reason:scaffold_complete` | authority | Scaffold is committed and pushed; the operator starts planning in a separate invocation. |
| `stop_reason:strict_confidence_opt_in` | authority | An opt-in `--strict` run stops before Phase 7 below the confidence threshold. |
| `stop_reason:speckit_cli_older` | authority | An answers-file scaffold found a SpecKit CLI older than the plugin pin. Upgrading the CLI is an operator action, and the answers file has no key for it. |
| `stop_reason:all_tiers_failed` | exhausted | All three escalation tiers failed. |
| `stop_reason:tier3_cap_reached` | exhausted | The per-run tier 3 cap is spent. |
| `stop_reason:tampering_or_forged_evidence` | harm_halt | Evidence or the ledger fails its hash or provenance check. |
| `stop_reason:secret_exposure` | harm_halt | A secret was exposed. |
| `stop_reason:identity_mismatch` | harm_halt | The run would write to the wrong repo, branch or worktree, or its workflow binding is ambiguous or unmatched. |
| `stop_reason:concurrent_writer` | harm_halt | Another live owner holds the run's ledger lock. |

Authority and exhausted reasons defer, except the operator-chosen boundaries,
`scaffold_complete`, `plan_stage_boundary` and `strict_confidence_opt_in`, which
end the run at the boundary the operator chose. `speckit_cli_older` is outside a run: it ends
an answers-file scaffold before any mutation. Harm halt reasons halt the run.

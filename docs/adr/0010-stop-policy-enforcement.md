# The runner enforces the stop policy; only harm halts end a run early

Status: accepted

Implementation status: planning decision; this ticket changes no plugin runtime behavior.

An autopilot run ends at one of two terminal states: planning ready for review (artifacts and draft PR ready) or ready for UAT. It ends earlier only for a harm halt, or pauses only for a security interrupt (owned by [Security interrupt: definition, runner receipt, question-tool hook per host](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1022)). Every other condition that stops a run today becomes an entry in the decisions list, or blocked-for-UAT work, and the run continues.

Decision: [Stop-policy enforcement: harm halts, fail-closed deferral, and the decisions list](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1015), part of [Wayfinder: speckit-pro health program](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1006).

## Enforcement

Today the policy is prose, hooks fail open, and an audit found about 45 stop sites, of which 9 map to a registered reason. The fix has two parts:

- **Runner gate.** The runner owns the closed registry. A run may end only when the runner reports a terminal state, a harm halt, or a security interrupt.
- **Stop hook on both hosts.** A Stop hook (Claude Code `Stop`, Codex `Stop`) asks the runner whether the run may end. Anything else blocks the turn end with the next step. A hook error fails closed (blocks). On Codex the hook needs persisted trust, which scaffold prepares and the readiness record reports (ADR 0008).

## Fail-closed deferral

A stop with no registered reason (a runner error, an agent ending its turn mid-run) is recorded as `unregistered_stop` against the check or unit it touched. That check climbs the retry ladder (ADR 0004); when the ladder is spent, its owning tasks become blocked-for-UAT and the run continues. Every occurrence enters the decisions list. The canary fails on any `unregistered_stop`, so each one is either registered or removed.

## Harm halts

A harm halt fires only when the next action could cause damage a later review cannot undo:

| Reason | Trigger |
| --- | --- |
| `secret_exposure` | A secret was exposed. |
| `tampering_or_forged_evidence` | Evidence or the ledger fails its hash or provenance check. |
| `identity_mismatch` | The run would write to the wrong repo, branch or worktree, including an ambiguous or unmatched workflow binding. |
| `concurrent_writer` | Another live owner holds the run's ledger lock. |

`integrity_failure` is removed; its cases are split into the reasons above or into deferrals below.

On a harm halt the runner stops all dispatch at once. No commit, push, PR edit or artifact publish follows the trigger, because a PR edit could spread a leaked secret. The runner writes a local halt record (reason, redacted trigger evidence, last safe state) and prints it. Resume is refused until a human clears the record with an explicit runner command.

## Former stop sites

| Today | Decision |
| --- | --- |
| `clock_moved_backwards` | Use the later of the last observed time and now as the clock floor; note it; continue. |
| Ledger lock held | Live owner: `concurrent_writer` harm halt. Owner gone: reclaim, note, continue. |
| Ledger unreadable after an interrupted write | Restore the last good snapshot, note, continue. A hash mismatch is `tampering_or_forged_evidence`. |
| `awaiting_external_event` | Gone mid-run: operator approvals are deleted (ADR 0004) and human UAT is a terminal state. |
| Dispatch left `unknown` (interrupted suite or agent) | Reconcile from git over the owned paths where possible; otherwise discard the dispatch's uncommitted changes to its owned paths and rerun. The interruption spends no ladder rung; a second interruption of the same dispatch counts as a failed attempt. |
| Corrective ceiling, infrastructure retry once per run, replan-epoch approval | Deleted with the retry ladder (ADR 0004). |
| Formal repair cap, formal tool unavailable | Retry ladder, then blocked-for-UAT (ADR 0005). |
| `scope_changing_pr_split` | A split recommendation in the decisions list; the full plan is built (ADR 0009). |
| `pr_missing`, recorded PR closed | Open a new draft PR from the run's branch; never reopen a closed PR; list the old record. |
| Several open PRs match the branch | Keep pushing the branch, edit none of them, open nothing new; list every candidate. |
| Session outside the workflow's worktree | Exactly one matching worktree: operate there by absolute path and note it. None or several: `identity_mismatch`. |
| Invalid or sample page cannot be deleted | Stage artifacts by explicit allowlist of current-run generated pages, so the page is never committed. It climbs the ladder, then is a visible gap. Push and draft PR proceed. |
| `tool_unavailable` | A readiness gap (ADR 0008); affected work uses the ladder. |
| Authority actions (merge, publish, protected push, secrets, destructive action, boundary-file edit, veto bypass, reopen closed PR) | Never taken; each attempt is an "authority action skipped" entry. |
| `all_tiers_failed` | Blocked-for-UAT (ADR 0004). |
| `tier3_cap_reached` | Deleted; there is no run-wide cap (ADR 0004). |
| `plan_stage_boundary` | Not a stop: it is the default planning run's terminal state. The stop-policy doc's claim that it does not apply to a default run is wrong. |
| `--strict` G6.5 below threshold | No longer stops planning. The run still produces artifacts and the draft PR, lists the low confidence first, and implement refuses to start until the plan approval record accepts it (detail with [Plan approval record](https://github.com/racecraft-lab/racecraft-plugins-public/issues/1014)). |
| `human_uat` | A terminal state, not a stop reason. |

Both plan-boundary fixes land in phase 2.

## The decisions list

The decisions list records every judgment the run made instead of asking. Each entry names the option chosen (the most conservative one that satisfies the spec), the rejected alternative, the evidence and the affected unit. Kinds include scope answers, readiness-stale notes, authority actions skipped, split recommendations, PR record problems and unregistered stops. Blocked-for-UAT work is a separate list that the decisions list links to. Nothing in it asks for a reply; the reviewer accepts or overturns entries at review.

The runner owns one file in run state as the single source. It renders first in the PR body, first in the UAT runbook and as a page in the HTML review artifacts. The final terminal message prints only the count and a link. Entries sort spec-affecting first, then authority skips, then notes. The canary receipt records the count per kind, so a growing list shows as a trend.

## Considered Options

- **Runner gate only, or canary detection only.** Rejected: an agent that just ends its turn would stop real runs; only a Stop hook catches it at the moment it happens.
- **Treat any untrustworthy state as a harm halt.** Rejected: local state the runner can rebuild (clock skew, a torn write, a stale lock) would end runs that could safely continue.
- **Unregistered stops go straight to blocked-for-UAT, or halt.** Rejected: the first loses repair attempts on transient errors; the second breaks the promise for every unmapped error.
- **Finalize the PR on a harm halt.** Rejected: posting to the PR after a secret exposure could spread it.
- **Keep the PR record stops.** Rejected: the branch is correct in each case, so building can continue safely without choosing a PR.
- **Keep `--strict` as a planning stop, or move it after the artifacts.** Rejected: plan approval is where a human already decides on the plan, so strict belongs there.
- **Merge decisions and blocked-for-UAT work into one list.** Rejected: one holds choices to review, the other holds work that was not built.

## Consequences

- The registry in `speckit_pro_runner/stop_policy.py`, `finalize-run` and the stop-policy reference change together; the parity test covers them.
- The canary asserts zero unregistered stops and records decisions-list counts per kind.
- [ADR 0012](0012-blocked-for-uat.md) defines blocked-for-UAT rendering immediately after the decisions list, preserving this ordering.

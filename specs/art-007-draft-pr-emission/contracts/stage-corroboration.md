# Contract: Stage-Resolution Corroboration

**Owner surface**: `speckit-pro/speckit_pro_runner/helpers/read_only.py`
(`resolve-autopilot-stage`), plus the Step 0.6c prose in both SKILL.md files.

Satisfies FR-011 and the FR-007 existence test, which share this status
vocabulary. Supports SC-005.

---

## 1. Division of labour

| Actor | Does | Never does |
| --- | --- | --- |
| Orchestrator | takes one read-only `gh` observation, passes it in as JSON | classifies, decides the stage |
| `resolve-autopilot-stage` | parses the `Draft PR` row, classifies, reports | runs `gh`, touches the network, changes the stage |

No helper in the runner shells out to `gh` today, and this contract preserves
that. The helper stays deterministic and offline-testable.

---

## 2. The observation

Taken by the orchestrator, exactly once per run, only when the `Draft PR` row is
present:

```bash
gh pr list --head <branch> --state all \
  --json number,url,state,isDraft,headRefName
```

Read-only. Scoped to the feature's head branch. Returns pull requests in every
state, which is what makes `pr_closed` distinguishable from `pr_missing`.

---

## 3. Input surface

`resolve-autopilot-stage` gains one optional `inputs` key. Argv is not used —
the runner reserves argv for `--help` and `--version` and reads one JSON request
from stdin.

```json
{
  "helper_id": "resolve-autopilot-stage",
  "operation": "resolve-autopilot-stage",
  "mode": "read_only",
  "inputs": {
    "workflow_file": "docs/ai/specs/.process/ART-007-workflow.md",
    "autopilot_args": ["--stage", "plan"],
    "pr_observation": {
      "ok": true,
      "pull_requests": [
        {"number": 438, "url": "https://github.com/o/r/pull/438",
         "state": "OPEN", "isDraft": true, "headRefName": "art-007-draft-pr-emission"}
      ]
    }
  }
}
```

| Key | Type | Meaning |
| --- | --- | --- |
| `pr_observation` | object, optional | Absent means no observation was supplied. |
| `pr_observation.ok` | boolean | `true` only when the query exited 0 and its output parsed. |
| `pr_observation.pull_requests` | array | The parsed `--json` array. Present only when `ok` is `true`. |
| `pr_observation.reason` | string | Why the query could not answer. Present only when `ok` is `false`. |

**Fail-closed on evidence, fail-open on outcome**: anything other than
`ok: true` with a parseable array yields `skipped`. The tool being absent,
unauthenticated, cancelled, rate-limited, or emitting unparseable output are all
the same class — none of them is evidence that a recorded pull request is gone.

---

## 4. Output surface

The eight existing keys are untouched. One object is added:

```json
{
  "tool": "resolve-autopilot-stage",
  "stage": "plan",
  "source": "argv",
  "basis": "explicit --stage plan",
  "recorded_stage": "plan",
  "planning_complete": false,
  "confidence_gate_status": "⏳ Pending",
  "from_phase": null,
  "corroboration": {
    "status": "match",
    "recorded": {"number": 438, "url": "https://github.com/o/r/pull/438"},
    "observed": {"number": 438, "url": "https://github.com/o/r/pull/438", "state": "OPEN"},
    "merged": null,
    "reason": null
  }
}
```

`corroboration` is **always present**, so a run that could not check is
distinguishable from a run that checked and agreed.

---

## 5. Classification

### 5.1 Preconditions, before any precedence rule runs

| Condition | Status | Observation taken? |
| --- | --- | --- |
| `Draft PR` row absent | `no_record` | no |
| Row present, `pr_observation` absent or `ok: false` | `skipped`, with `reason` | attempted or not |
| Row present, observation `ok: true` and parseable | run §5.2 | yes |

### 5.2 Precedence, first match wins

| # | Condition | Status | Extra |
| --- | --- | --- | --- |
| 1 | An open pull request exists on the head branch whose number differs from the recorded number | `identity_mismatch` | `observed` names the open one |
| 2 | The recorded number is open, but its live URL differs from the recorded URL | `identity_mismatch` | `observed` carries the live URL |
| 3 | The recorded number's live state is closed or merged | `pr_closed` | `merged` is `true` or `false` |
| 4 | The recorded number is absent from the observation | `pr_missing` | `observed` is null |
| 5 | Anything else | `match` | — |

The order is load-bearing. Rule 1 before rule 4 means a branch that grew a second
pull request reports the conflict rather than the absence.

### 5.3 Closed vocabulary

`match`, `no_record`, `skipped`, `pr_closed`, `pr_missing`, `identity_mismatch`.
Exactly six, no aliases, no alternate casing. The last three are discrepancies;
the first three are not.

---

## 6. Sinks

| Sink | Carries | When |
| --- | --- | --- |
| stage-resolution envelope | the full `corroboration` object | always |
| run report | one line naming the status, beside the `Stage:` line Step 0.6c already prints | always |
| workflow file, Step 0.6c record | that same line | discrepancies only |

The durable write lands in the same edit turn as the `Stage` row, so it reaches
the same commit — the write-cadence rule the shipped protocol already sets for
`Stage`. `match`, `no_record`, and `skipped` write nothing durable, and the
scaffold workflow template ships no placeholder line.

**Run-report line shape**, matching the existing one-line convention:

```text
Stage: plan (argv) — explicit --stage plan
Draft PR: match — #438 recorded, #438 observed
```

```text
Draft PR: skipped — gh not authenticated
Draft PR: pr_closed — #438 recorded, closed (merged: false)
```

---

## 7. Consequences at the terminal step

| Status | Terminal-step behaviour |
| --- | --- |
| `match` | refresh the existing pull request's description, and its title if it changed; report that URL |
| `no_record` | fall through to the live by-branch existence test, then create or refresh |
| `skipped` | fall through to the live by-branch existence test, then create or refresh |
| `identity_mismatch` | do not create; log; stop report names both identities and the manual resume path |
| `pr_closed` | do not reopen, do not create a second one; leave the row unchanged; stop report names the number, URL, `gh pr reopen <number>`, and re-run |
| `pr_missing` | do not create, do not rewrite the row; stop report names the recorded identity and "correct or clear the row, then re-run" |

The three discrepancy responses end the emission attempt fail-open. They do not
invoke FR-006's strict-mode blocked-stop contract, and they never mutate GitHub.

**Never**: change the resolved stage, block stage resolution, stop the run at
resolution time, reopen a pull request, or open a second one.

---

## 8. Test obligations

| Obligation | Where |
| --- | --- |
| Each of the six statuses is produced by its own input | `tests/speckit-pro/unit/test-autopilot-stage-resolution.py` |
| Precedence: an extra open PR outranks a missing recorded number | same |
| `ok: false` yields `skipped` and never a discrepancy, for each reason class | same |
| An absent `Draft PR` row yields `no_record` and takes no observation | same |
| A malformed observation yields `skipped`, not a traceback | same |
| The resolved `stage` is identical with and without the observation | same |
| The eight pre-existing envelope keys are unchanged | same, existing assertions |

Tests build workflow-file text in memory, as the shipped stage-resolution suite
already does. No new fixture files are needed for this contract.

# CAR-004 live smoke runbook (operator, by hand)

This covers task **T062** — the one part of CAR-004 that a person has to run.
Everything else in this feature is deterministic and already runs in CI.

You do not need to have built any of this. Follow the steps in order.

## What this is

CAR-004 adds three "policy controls" — three different ways of choosing which
model handles a piece of work:

| Control | Plain meaning |
|---|---|
| `unpinned` | Do not choose. Inherit whatever the parent session is pinned to. |
| `adaptive` | Start low, and step up one rung when the work turns out to be harder. |
| `orchestration-changing` | Fan the work out to several children at once, then add up what they used. |

The deterministic tests prove the *rules* about these controls hold. They cannot
prove the behaviour actually happens on a live platform. That is what these three
runs are for: one short, bounded, real run per control.

**Nothing you produce here is committed.** Output lands under
`tests/speckit-pro/layer6-efficiency/results/`, which is already git-ignored.

## Before you start

1. **Python 3.11 or newer** on `PATH`. Nothing to install — no packages, no
   virtualenv, no `jq`.
2. **This worktree, on the `car-004-policy-controls-comparators` branch.** Never
   run this from `main`. All commands below are run from the worktree root and
   all paths are relative to it.
3. **An authenticated Claude subscription session.** This is the only supported
   authentication path.
4. **No API key anywhere in the environment.** Unset `ANTHROPIC_API_KEY` (and any
   equivalent) in the shell you run from. A run observed on an API key is refused
   as evidence — see step 9.
5. **Do not set a subagent model override.** Each run has to record that the
   override was left unset; with it set, the run cannot prove anything about
   routing because the override, not the control, chose the model.
6. **Never run this in CI.** The driver is deliberately absent from
   `tests/speckit-pro/suite-manifest.json` for that reason.

Budget roughly 20 to 40 minutes of attention for all three runs.

## The four bounds every run must stay inside

These are frozen. They are counted over the whole **unit** — the parent plus any
children it spawned — not per dispatch.

| Bound | Limit | How it is counted |
|---|---|---|
| Non-reserved objectives | **at most 5** | One per objective *attempt*. A child dispatch does **not** consume one. |
| Repetitions | **1** | Each objective is attempted once. No re-running the same objective. |
| Raw tokens | **1,000,000** | Summed across every member of the unit. |
| Wall clock | **30 minutes (1800 s)** | *Elapsed* time over the unit, not the sum of each member's duration. |

A run that reaches a bound and stops there is still valid evidence. A run that
goes past one is refused at seal time.

There are additional frozen ceilings (per-token-class and cache quantities) that
the plan prints in step 2. You do not need to plan around them; the seal step
checks them for you.

## What each run has to actually show

Seal time will not take your word for it. Each control has one observable that
must be **read back from what the run produced**, never from what the dispatch
asked for:

| Control | The observable that proves it |
|---|---|
| `unpinned` | The served model and effort are **equal to the pinned parent session's**, read out of the configured-route proof. |
| `adaptive` | The served model, effort, and route id **moved from ladder rung *i* to rung *i+1***, read out of the configured-route proof. Matching route ids alone are not enough — the served model and effort have to move with them. |
| `orchestration-changing` | **At least two non-parent members**, and the parent's wall time is **strictly less** than the sum of the children's wall times. That inequality is what proves they really ran in parallel. Every wall time must be recorded; a missing one is not read as zero. |

---

## Steps

### 1. Confirm the deterministic baseline is green

```bash
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expected:** both pass. If either is red, stop — that is an environment problem,
and a later failure would not be attributable to the live run.

### 2. Print the bounded plan for the first control

Run the three controls **in sequence**: `unpinned`, then `adaptive`, then
`orchestration-changing`. Start with `unpinned`.

```bash
python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \
    --control unpinned --plan
```

**Expected:** a plan block naming the control id, its content digest, the
partition `CAR-004-SMOKE`, five objective ids, every frozen bound, and a
`demonstrate:` line describing the observable from the table above. It prints and
exits — it dispatches nothing.

The objective list is the frozen consumption path's own answer, so a reserved
objective can never be handed to you in the first place. Use only the objectives
the plan printed.

### 3. Make a fresh, empty cache root for this run only

Each of the three runs gets its **own** cache root, so no run warms another one's
cache. Create a new empty directory outside the repository and launch this run's
agent session against it, using whatever configuration directory your CLI reads.

Then record its digest — the record stores a **hash**, never the path:

```bash
python3 -c "import hashlib,sys;print('sha256:'+hashlib.sha256(sys.argv[1].encode()).hexdigest())" "$CACHE_ROOT"
```

**Expected:** a `sha256:` line. Keep it; you need it in step 5 and step 10. A
record that carries a filesystem path instead of a digest is rejected.

### 4. Execute the plan by hand

Work through the printed objectives, in one sitting, on the subscription session.
Stay inside the four bounds. Stop at the first bound you reach.

**Expected:** the work completes, or it stops cleanly at a bound. Either is fine.
While it runs, note the things you will have to write down in step 5 — most
importantly the elapsed wall clock and each unit member's wall time.

### 5. Write the run record

Write a JSON file (anywhere outside the repository — it is an input, not an
artifact). Every field below is required:

```json
{
  "record_kind": "policy_control_smoke",
  "schema_version": "1.0.0",
  "smoke_id": "car-004-smoke-unpinned",
  "arm_id": "car-004-unpinned-control",
  "control_id": "car-004-unpinned-control",
  "control_digest": "<the control_digest the plan printed>",
  "authentication_mode": "subscription",
  "scored": false,
  "partition_id": "CAR-004-SMOKE",
  "objective_ids": ["<the objectives you actually attempted>"],
  "confirmation_entries": 0,
  "elapsed_wall_clock_seconds": 0,
  "claude_code_subagent_model_unset": true,
  "objective_attempts": [
    {
      "objective_id": "<objective id>",
      "unit_rows": [
        {
          "row_id": "<any stable id>",
          "spawned_by": null,
          "wall_time_ms": 0,
          "duration_ms": 0,
          "raw_token_vector": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_input_tokens": 0,
            "reasoning_output_tokens": 0
          },
          "cache_diagnostic": {
            "cache_write_tokens_by_ttl_class": {"ephemeral_5m": 0, "ephemeral_1h": 0},
            "cache_read_tokens": 0
          }
        }
      ]
    }
  ],
  "observed_cache_isolation": [],
  "demonstration_state": "demonstrated",
  "demonstration_evidence": {
    "read_back_from": "configured_route_proof",
    "served_route": {"model": "...", "effort": "...", "candidate_route_id": "..."}
  }
}
```

Notes that matter:

- Exactly **one** row per attempt has `"spawned_by": null` — that is the parent.
  Children carry the parent's `row_id` there.
- `wall_time_ms` and `duration_ms` are different quantities on purpose. Wall time
  is what the parallel check reads; duration is the additive one.
- `read_back_from` must be `configured_route_proof` or `execution_trace`. The
  value `dispatch_request` is refused by design — asking for a route is not
  evidence that the route was served.
- `demonstration_evidence` differs per control:
  - `unpinned` → `served_route`
  - `adaptive` → `pre_escalation` **and** `post_escalation`, each with `model`,
    `effort`, `candidate_route_id`
  - `orchestration-changing` → `{"read_back_from": "execution_trace"}`; the proof
    comes from the unit rows' wall times.
- Record what you observed. Do not write `"demonstrated"` hopefully — the seal
  step derives the state from the evidence and reports it when your label
  disagrees.

### 6. Seal the record

```bash
python3 tests/speckit-pro/layer6-efficiency/run-control-smoke.py \
    --control unpinned --seal <path-to-your-record.json>
```

**Expected on success:** exit code 0 and a line
`sealed: tests/speckit-pro/layer6-efficiency/results/<smoke_id>.json`.

**Expected on refusal:** exit code 2, `REFUSED as FR-031 evidence: [...]` on
stderr with the reason, **and the record is still written** under `results/` with
its observed values intact. A refused run stays distinguishable from a run that
never happened. The remedy is always a re-run — never editing the record to make
it pass.

The four things that get a record refused: an observed API key, a scored row, any
reference to the reserved partition, and a breached bound.

### 7. Repeat for `adaptive`

Steps 2 through 6, with `--control adaptive`, under a **new** cache root. The
demonstration evidence needs both `pre_escalation` and `post_escalation`.

**Expected:** sealed, with the post-escalation route exactly one rung above the
pre-escalation route and a served model or effort that actually changed.

### 8. Repeat for `orchestration-changing`

Steps 2 through 6, with `--control orchestration-changing`, under a **third** new
cache root. This run needs at least two children.

**Expected:** sealed, with the parent's wall time strictly below the children's
summed wall times.

### 9. Confirm all three ran on the subscription path

Read it back from the three sealed files rather than from memory:

```bash
python3 -c "
import json,pathlib
for p in sorted(pathlib.Path('tests/speckit-pro/layer6-efficiency/results').glob('car-004-smoke-*.json')):
    d=json.loads(p.read_text())
    print(p.name, d['evidence_admissibility'], d['authentication_mode'],
          d.get('demonstration',{}).get('demonstration_state'),
          d.get('demonstration',{}).get('claude_code_subagent_model_unset'))
"
```

**Expected:** three lines, each `admitted subscription demonstrated True`.
Anything else is a re-run, not a relabel.

### 10. Prove the three cache roots were disjoint

The isolation claim is over **all three unordered pairs** — unpinned/adaptive,
adaptive/orchestration, and unpinned/orchestration. Checking only consecutive
runs would leave the first-to-last pair unchecked.

Each record's `observed_cache_isolation` list needs one entry per *other* arm,
carrying `paired_arm_id`, `status: "observed_disjoint"`, `roots_disjoint: true`,
`arm_cache_root_digest`, and `paired_arm_cache_root_digest` — the digests from
step 3. A stated intention to isolate is not accepted as evidence that isolation
happened.

```bash
python3 -c "
import json,pathlib,sys
sys.path.insert(0,'tests/speckit-pro/layer6-efficiency/lib')
import claude_policy_controls as c
series=[json.loads(p.read_text()) for p in
        sorted(pathlib.Path('tests/speckit-pro/layer6-efficiency/results').glob('car-004-smoke-*.json'))]
print(json.dumps(c.evaluate_cache_isolation(series), indent=2))
"
```

**Expected:** `"all_pairs_disjoint": true`, three entries under `pairs`, and an
empty `invalidated_arms`.

### 11. Confirm nothing leaked into the change set

```bash
git status --porcelain tests/speckit-pro/layer6-efficiency/results/
```

**Expected:** no output at all.

### 12. Close the task

Tick `T062` in `specs/car-004-policy-controls-comparators/tasks.md` and note the
run date. If you are merging **without** running these smokes, say so plainly in
the PR body and name the success criteria that stay unevidenced (SC-009, SC-026,
SC-027, SC-029, SC-030, SC-031). An unrun smoke is an honest gap; a fabricated
one is not.

## If something goes wrong

| What you see | What it means |
|---|---|
| The seal step refuses | Read the reason. It is one of: API-key authentication, a scored row, a reserved-partition reference, or a breached bound. All four are fail-closed on purpose. |
| `observable_read_from_dispatch_request` | The evidence was taken from the request instead of from what the run produced. Re-run and read back from the configured-route proof or the execution trace. |
| `subagent_model_override_not_excluded` | A subagent model override was set. The run cannot show anything about routing; re-run with it unset. |
| `wall_time_unobserved` | At least one unit member has no `wall_time_ms`. A missing value is never read as zero, because that would make the parallel check trivially true. |
| `route_did_not_advance_one_ladder_entry` | The adaptive run did not step exactly one rung. Two rungs, no rung, or a wrap-around all fail. |
| A digest mismatch on `unpinned` | The pinned parent binding is wrong. Two frozen documents answer to "environment contract"; the right one is the Claude-side `environment_contract` object in `tests/speckit-pro/layer6-efficiency/contracts-claude/experiment-assignment.schema.json`. |

Deeper background, including the full section 5 verification table, lives in
`specs/car-004-policy-controls-comparators/quickstart.md`.

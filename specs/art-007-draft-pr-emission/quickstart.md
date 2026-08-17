# Quickstart: Validating Draft-PR Emission (ART-007)

**Branch**: `art-007-draft-pr-emission` | **Date**: 2026-08-17

Seven scenarios that prove the feature works end to end. Run them from the
repository root. Scenarios 1 through 4 are deterministic and need no network.
Scenarios 5 through 7 exercise the pull-request boundary and need an
authenticated `gh`.

Contract details live in `contracts/`; entity shapes live in `data-model.md`.
Nothing is duplicated here.

---

## Prerequisites

- Python 3.11 or newer on `PATH`. No package installation, no virtualenv.
- A fresh worktree needs no bootstrap for the test suite.
- Scenarios 5 to 7 additionally need `gh` installed and authenticated against a
  repository fork you are willing to open and close draft pull requests on.

---

## The single verification command

```bash
python3 tests/speckit-pro/run-all.py
```

This is both UNIT_TEST and FULL_VERIFY for this repository. Layers 1, 4, and 5
run by default and must finish with zero failures. There is no build, typecheck,
or lint step — the stack is Markdown, JSON, and standard-library Python.

To iterate faster on one surface while working:

```bash
python3 tests/speckit-pro/run-all.py --layer 4   # helpers, schemas, fixtures
python3 tests/speckit-pro/run-all.py --layer 1   # structural and payload
```

Run the full command before calling any task done.

---

## Scenario 1 — A draft packet validates without implementation evidence

**Proves**: FR-005.

Build the request inline against the declared fixture. Do not add a request
fixture under `fixtures/read-only-helpers/requests/` — that directory is bound by
a fixture manifest, and restaling it is unrelated cost.

```bash
cat <<'JSON' | PYTHONPATH=speckit-pro python3 -m speckit_pro_runner
{"schema_version":"1.0","request_id":"draft-check",
 "helper_id":"validate-pr-packet-read-only",
 "operation":"validate-pr-packet-read-only","mode":"read_only",
 "inputs":{"packet_path":"tests/speckit-pro/unit/fixtures/pr-packet/valid-draft.json"}}
JSON
```

**Expect**: the response envelope carries `status` `ok` and `exit_code` `0`, and
`data.stdout_json.status` reads `passed` with `pr_blocked` false — for a packet
carrying `"mode": "draft"`, an empty `verification_evidence`, an empty
`scope_evidence.changed_files`, and an empty `uat.how_to_uat`.

**Fails if**: the schema was relaxed but the validator's two hand-written
evidence assertions were not. That is the most likely single defect in this
feature; this scenario is the tripwire for it.

---

## Scenario 2 — The two shipped modes are untouched

**Proves**: SC-008.

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expect**: every pre-existing `pr-packet` fixture reports the same outcome it
reported before the change — one valid `single`, six invalid `single` variants,
one valid `split`. Not one assertion in the existing packet tests changes.

**Fails if**: a relaxation leaked outside the `mode == "draft"` branch. A green
draft test beside a changed `single` expectation is a regression, not a pass.

---

## Scenario 3 — Corroboration produces each of the six statuses

**Proves**: FR-011.

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expect**: `test-autopilot-stage-resolution` covers each status from its own
input and asserts, for every one of them, that the resolved `stage` is identical
to what the same workflow file resolves to with no observation supplied at all.

Spot-check the classification by hand with a request whose `inputs` carry a
`workflow_file` holding a `Draft PR` row and a `pr_observation`:

| Observation | Expected `corroboration.status` |
| --- | --- |
| the recorded number, open, matching URL | `match` |
| the recorded number, state closed | `pr_closed` with `merged` false |
| an empty `pull_requests` array | `pr_missing` |
| a different open number on the head branch | `identity_mismatch` |
| `{"ok": false, "reason": "gh not authenticated"}` | `skipped`, reason echoed |
| workflow file with no `Draft PR` row | `no_record` |

**Fails if**: any input path changes `stage`, or any unsuccessful observation
produces a discrepancy instead of `skipped`.

---

## Scenario 4 — The new agent ships on both platforms and breaks no digest

**Proves**: FR-001, and the Out-of-Scope corpus boundary.

```bash
python3 scripts/refresh-release-artifacts.py
python3 tests/speckit-pro/run-all.py --layer 1
python3 tests/speckit-pro/run-all.py --layer 4
```

**Expect**:

- `speckit-pro/agents/artifact-author.md` and
  `speckit-pro/codex-agents/artifact-author.toml` both pass the payload
  frontmatter sweep.
- Claude/Codex agent existence parity passes.
- The Layer 6 corpus governance test still reports exactly twelve roles, and no
  `source digest does not match role source bytes` failure appears. That error
  would mean a governed agent definition was edited, which this feature forbids.
- The Codex install helper accepts the bundle. If it reports
  `incomplete_agent_bundle` naming `artifact-author.toml` as unexpected, the
  frozen filename set in the install helper was not updated.

Note that `refresh-release-artifacts.py --check` compares against the **committed**
tree, so it exits 1 on a regeneration that is correct but not yet committed. That
exit is expected and resolves on commit.

---

## Scenario 5 — A pass run ends at an open draft pull request

**Proves**: User Story 1, FR-003, FR-006 (pass arm), FR-007, FR-008, FR-009,
FR-010, FR-013, SC-001, SC-002, SC-006, SC-007.

**Setup**: a feature branch whose planning phases are complete and whose final
confidence gate resolves pass or warn.

**Run**: the plan stage to completion.

**Expect, in this order**:

1. Artifact pages exist under `specs/<branch>/artifacts/`.
2. One stage-boundary commit, message `chore(SPEC-XXX): close the plan stage
   boundary`, staging `specs/`, the workflow file, and the state file — and
   nothing else. Its message, path set, and non-emptiness are unchanged from
   before this feature.
3. The branch is pushed.
4. `gh pr view --json isDraft,title,body` on the branch reports `isDraft` true.
5. The title matches `<type>(<lowercase-scope>): <plain English description>`.
   Confirm it independently:

   ```bash
   python3 -m speckit_pro_runner   # validate-pr-title, with the emitted title
   ```

6. The body contains exactly an artifacts index table and a resume/status block.
   It contains no release-note fence and no verification section. Confirm the
   absence directly:

   ```bash
   gh pr view --json body --jq '.body' | grep -c 'release-note' || true
   ```

   Expect `0`.
7. The workflow file's `### Basic Information` table carries one `Draft PR` row
   whose value begins with `[#<number>](<url>)`, and the `## Workflow Overview`
   table gained no row.
8. A second, separate bookkeeping commit carries that row.
9. The stop report carries the URL, the artifact index, and the resume
   instruction — and nothing else is needed to hand off.

**Also run the warn arm**: with the gate resolving warn, every step above is
identical. Emission does not distinguish pass from warn.

---

## Scenario 6 — A strict-mode block opens no pull request

**Proves**: FR-006, SC-004.

**Setup**: the same branch, with the final gate resolving blocked under strict
mode.

**Expect**:

- No pull request exists for the branch.
- The stage-boundary commit is still taken, with its message and path set
  unchanged.
- The `Confidence Gate` row is non-terminal blocked.
- The stop report names the blocking gate in place of a URL.
- The `Draft PR` row is absent, and its absence is not reported as an error.

**Fails if**: emission ran at all. The short-circuit is a return before
generation, not a wrapper around it, so a blocked run must not even write
artifacts.

---

## Scenario 7 — Fail-open and re-entry

**Proves**: FR-004, FR-007, FR-011 discrepancy responses, SC-003, SC-005.

Four sub-runs against the same branch:

**7a. Zero artifacts.** Make every selected template unreadable, then run a pass
stage. Expect: the draft pull request still opens; its index carries gap rows
only; the shortfall appears in the stop report and after the link in the
workflow file's `Draft PR` cell. Three sinks, all populated.

**7b. Partial generation.** Make one template unreadable. Expect: the successful
pages are indexed normally, the failed one appears as a gap row, and the run is
not treated as a failure.

**7c. Re-entry with an open pull request.** Run the stage again. Expect: no
second pull request; the existing description is refreshed; the reported outcome
names the existing URL. Then delete the `Draft PR` row and re-run — expect the
same result, because the live by-branch query is the second half of the existence
test and either positive proves one exists.

**7d. Re-entry with a closed pull request.** Close the pull request manually,
leave the row in place, and re-run. Expect: no reopen, no second pull request,
the row untouched, a `pr_closed` discrepancy logged, and a stop report naming the
number, the URL, `gh pr reopen <number>`, and re-run the stage.

---

## Green means

```text
python3 tests/speckit-pro/run-all.py     →  zero failures across Layers 1, 4, 5
Scenario 5                               →  a draft PR whose body indexes the artifacts
Scenario 6                               →  no PR, and a stop report naming the gate
Scenario 7                               →  a PR every time the gate passed, gaps visible in all three sinks
```

Before calling the work done, confirm the generated-artifact contract was
honoured: plugin source changed, so `python3 scripts/refresh-release-artifacts.py`
must have run and its output committed. CI's `artifact-consistency` job fails the
pull request otherwise.

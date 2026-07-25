# Quickstart: G56R-003 Evaluation Platform

This is the planned operator and verification contract. Commands that target
the new qualification adapter become executable during implementation. The
legacy smoke runner remains available but does not produce qualification
evidence.

## 1. Verify deterministic contracts

From the repository root:

```bash
python3 tests/speckit-pro/unit/test-agent-materialization.py
python3 tests/speckit-pro/unit/test-codex-successor-capability.py
python3 tests/speckit-pro/unit/test-codex-qualification-contracts.py
python3 tests/speckit-pro/unit/test-codex-qualification-corpus.py
python3 tests/speckit-pro/unit/test-codex-qualification-scoring.py
python3 tests/speckit-pro/unit/test-codex-qualification-statistics.py
```

These tests are local, deterministic, and network-free.

## 2. Replay frozen evidence

The planned replay command reads committed sanitized bundles only:

```bash
python3 tests/speckit-pro/layer6-efficiency/run-codex-qualification.py \
  replay \
  --experiment-bundle tests/speckit-pro/layer6-efficiency/replay/experiment.json \
  --score-bundle-dir tests/speckit-pro/layer6-efficiency/replay/scores \
  --analysis-plan tests/speckit-pro/layer6-efficiency/replay/analysis-plan.json \
  --expected-decision tests/speckit-pro/layer6-efficiency/replay/decision.json
```

Replay must:

- validate every ID/digest join;
- reject stale, mixed-partition, identity-revealing, or incomplete evidence;
- recompute the terminal decision;
- match the expected decision ID and digest byte-for-byte;
- perform no network request and write no live evidence.

## 3. Inspect the pinned runtime catalog

Catalog inspection is explicit and local:

```bash
codex debug models
```

The qualification collector invokes the pinned command contract with argument
arrays and captures raw bytes directly into the operator-only
content-addressed retention store. Do not redirect raw output into the
repository.

## 4. Publish an additive successor freeze

After collecting raw evidence outside Git, the planned publication command is:

```bash
python3 tests/speckit-pro/layer6-efficiency/run-codex-qualification.py \
  publish-successor-freeze \
  --source-ledger docs/ai/research/codex-agent-route-candidate-manifest.json \
  --catalog-evidence-ref sha256:<operator-retained-digest> \
  --output tests/speckit-pro/layer6-efficiency/replay/successor-freeze.json
```

Publication succeeds only when:

- the source ledger and runtime collection are current and trusted;
- the normalized intersection is non-empty;
- every admitted tuple is source-admitted and runtime-supported;
- the committed output passes the deny-by-default sensitive-field allowlist;
- all G56R-002 artifacts remain unchanged.

An empty or invalid collection records a failure outside the authoritative
freeze path and exits nonzero.

## 5. Run the explicit calibration-only pilot

Live execution is never a default CI action. The operator must provide a
calibration partition, a pinned successor freeze, a frozen experiment policy,
an explicit budget, and an operator-only raw evidence root:

```bash
python3 tests/speckit-pro/layer6-efficiency/run-codex-qualification.py \
  calibrate \
  --partition tests/speckit-pro/layer6-efficiency/calibration/partition.json \
  --candidate-freeze tests/speckit-pro/layer6-efficiency/calibration/successor-freeze.json \
  --experiment-policy tests/speckit-pro/layer6-efficiency/calibration/experiment-policy.json \
  --corpus tests/speckit-pro/layer6-efficiency/fixtures-codex/corpus-manifest.json \
  --budget tests/speckit-pro/layer6-efficiency/calibration/budget.json \
  --raw-evidence-root /absolute/operator-controlled/path
```

Before the first live call, the adapter must print and require confirmation of:

- pinned client/build and runtime snapshot IDs;
- `partition_type=calibration`;
- `qualification_eligible=false`;
- attempt, token, duration, and cost ceilings;
- scorer/adjudicator and rubric versions;
- raw retention root outside the repository;
- complete-pair rerun cap.

The command must refuse screening, selection, cohort-lock, or integrated
confirmation partitions. It must never emit final route policy.

## 6. Raw evidence retention

Raw catalog bytes, prompts, responses, transcripts, personal scorer mappings,
account/auth/session data, private hosts, absolute local paths, repository
remotes, and billing/plan data stay in the inherited operator-only
content-addressed store.

Committed output may contain only:

- opaque IDs and digests;
- sanitized client/boundary metadata;
- normalized tuple decisions;
- relative repository bindings;
- deterministic fixtures and oracles;
- anonymized ballots and sanitized rationales;
- score, analysis, and decision bundles;
- content-addressed evidence refs.

Run the sensitive-field validator before adding any evidence file. Unknown
fields block publication; do not manually redact around the validator.

## 7. Freeze the numeric analysis plan

After the calibration report is independently reviewed, create a versioned
plan that records all required numeric and terminal rules:

```bash
python3 tests/speckit-pro/layer6-efficiency/run-codex-qualification.py \
  freeze-analysis-plan \
  --calibration-report tests/speckit-pro/layer6-efficiency/calibration/report.json \
  --draft-plan tests/speckit-pro/layer6-efficiency/calibration/analysis-plan-draft.json \
  --output tests/speckit-pro/layer6-efficiency/calibration/analysis-plan.json
```

The freeze must prove that no G56R-007 through G56R-010 outcome-bearing
evidence existed at the freeze point. Later changes create a new plan and
invalidate dependent decisions; they never mutate the old plan.

## 8. Refresh shipped runner artifacts

When `speckit-pro/speckit_pro_runner/agent_materialization.py` changes:

```bash
python3 scripts/refresh-release-artifacts.py
python3 scripts/refresh-release-artifacts.py --check
```

Review the generated runner trust metadata, payloads, installed-cache proofs,
and release evidence together. Never hand-edit those outputs.

## 9. Run repository gates

Focused Layer 4 verification:

```bash
python3 tests/speckit-pro/run-all.py --layer 4
```

Full authoritative suite:

```bash
python3 -u tests/speckit-pro/run-all.py
```

Before PR publication, validate the exact final PR title with the repository
release-readiness gate. The title must match:

```text
<type>(<lowercase-scope>): <plain English description>
```

## Expected failure behavior

- non-authoritative or empty successor collection: no freeze publication;
- treatment proof failure or reroute: immutable non-scorable trace;
- deterministic hard-gate failure: no semantic ballots;
- stale/non-blind/duplicate scorer ballot: invalid score bundle;
- mixed partition or incomplete pair: inconclusive/no qualification;
- candidate-caused terminal event: retained with acceptance zero;
- independently proven transient harness failure: capped full-pair rerun only;
- calibration decision request: calibration result only, never qualification.

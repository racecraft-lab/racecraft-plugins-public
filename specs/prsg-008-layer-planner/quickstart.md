# Quickstart: PRSG-008 Layer Planner Validation

This guide defines the validation scenarios for the PRSG-008 implementation.
Commands run from the repository root.

## Prerequisites

- `bash`
- `jq`
- Existing repository test harness under `tests/speckit-pro/`

## Scenario 1: Valid Plan Emits Stable JSON

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real \
  > /tmp/plan-layers-valid.json
```

Expected result:

- Exit code `0`
- Stdout is valid JSON
- `.status == "ok"`
- `.increments` contains ordered semantic IDs such as `foundation`, `us1`,
  and `polish`
- `[P]` tasks appear with `"parallel": true`
- Checkbox state appears as `todo` or `done`

## Scenario 2: Deterministic Output

```bash
for run in 1 2 3 4 5; do
  bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
    tests/speckit-pro/layer4-scripts/fixtures/plan-layers/valid-real \
    > "/tmp/plan-layers-$run.json"
done

cmp /tmp/plan-layers-1.json /tmp/plan-layers-2.json
cmp /tmp/plan-layers-1.json /tmp/plan-layers-3.json
cmp /tmp/plan-layers-1.json /tmp/plan-layers-4.json
cmp /tmp/plan-layers-1.json /tmp/plan-layers-5.json
```

Expected result:

- All five outputs are byte-for-byte identical.

## Scenario 3: Invalid Plans Stop with Exit 1

Run the malformed fixtures:

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  tests/speckit-pro/layer4-scripts/fixtures/plan-layers/missing-headings

bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  tests/speckit-pro/layer4-scripts/fixtures/plan-layers/dependency-cycle

bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  tests/speckit-pro/layer4-scripts/fixtures/plan-layers/empty-increment
```

Expected result for each:

- Exit code `1`
- Stdout is valid JSON
- `.status == "invalid_plan"`
- `.errors[].code` uses the contract enum
- Stderr contains a concise human-readable summary

## Scenario 4: Warnings Do Not Fail Otherwise Valid Plans

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  tests/speckit-pro/layer4-scripts/fixtures/plan-layers/invalid-reference \
  > /tmp/plan-layers-warning.json
```

Expected result:

- Exit code `0`
- `.status == "ok"`
- `.warnings[].code` includes `reference_not_found`
- Missing-reference details identify `kind` as `file` or `test`

## Scenario 5: Usage/Input Errors Stop with Exit 2

```bash
bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh

bash speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh \
  /path/that/does/not/exist
```

Expected result:

- Exit code `2`
- Stdout is valid JSON
- `.status == "input_error"`
- No repository files are created, modified, moved, or deleted

## Scenario 6: Autopilot Handoff

Use an autopilot fixture where PRSG-007 records route `split-PR`.

Expected result:

- Autopilot runs the planner after post-G5 route recording and before Analyze or
  implementation prompt construction.
- Planner exit `0` persists the full envelope to `autopilot-state.json`, writes
  a concise workflow `## Layer Plan` summary, and continues.
- Planner exit `1` emits the fixed invalid-plan stop line from the spec and
  stops before implementation.
- Planner exit `2` emits a distinct input-error stop line and stops before
  implementation.

## Repository Validation

```bash
bash tests/speckit-pro/run-all.sh --layer 1
bash tests/speckit-pro/run-all.sh --layer 4
bash tests/speckit-pro/run-all.sh
```

Expected result:

- Layer 1, Layer 4, and the default deterministic suite pass.

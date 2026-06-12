# Quickstart: Non-Stopping Reviewability Markers

## Prerequisites

- Work from branch `prsg-013-reviewability-markers`.
- Ensure `bash`, `jq`, `git`, and the repository test harness are available.
- Use the contracts in `specs/prsg-013-reviewability-markers/contracts/` as the planning reference for marker-plan and final-backstop evidence.

## Validation Scenarios

### 1. Structural validation

Run:

```bash
bash tests/speckit-pro/run-all.sh --layer 1
```

Expected outcome:

- Plugin layout, skills, hooks, agents, command docs, and contracts remain structurally valid.

### 2. Marker planning from task structure

Run the Layer 4 tests after implementation:

```bash
bash tests/speckit-pro/run-all.sh --layer 4
```

Expected outcome:

- Foundation tasks create a `foundation` marker only when present.
- Each user-story section creates one marker before subdivision.
- Small Polish tasks fold into a nearby non-Polish marker.
- Marker IDs follow `foundation`, `us<N>`, `us<N>-part<M>`, or `full-spec`.
- `markers[]` order and one-based `review_order` are authoritative.
- The marker plan is persisted as top-level `pr_marker_plan` state and workflow evidence without rewriting `tasks.md`.

### 3. Non-stopping task reviewability result

Use a fixture where `reviewability-gate.sh tasks` emits valid `status=block` JSON for size only and exits nonzero.

Expected outcome:

- Autopilot captures stdout and exit code.
- The valid size-only block becomes marker-planning input.
- Implementation continues.
- Malformed JSON, missing status or mode, unreadable evidence, failed verification, invalid packets, or unsafe output still stop.

### 4. Oversized story subdivision

Use two fixtures:

- A user story with safe contiguous task clusters.
- A user story with dependency crossing or shared mutation hazards.

Expected outcome:

- Safe clusters create ordered `us<N>-part<M>` markers.
- Unsafe clusters keep the original `us<N>` marker.
- The unsafe case records a structured warning with `code`, `severity`, `message`, `source`, and `details`.

### 5. Hazard collapse

Use atomicity fixtures for:

- `route == single-atomic-PR`
- `releasable == false`
- `route == one-navigable-PR` with `releasable == true`

Expected outcome:

- The first two cases collapse PR emission to `full-spec` with warnings and source marker evidence.
- `one-navigable-PR` with `releasable == true` does not collapse by itself.
- Implementation still checkpoints original markers in order before collapsed emission.

### 6. Final backstop marker split

Use a fixture where the final full diff is size-blocked and the current `pr_marker_plan` is valid.

Expected outcome:

- Final backstop emits outcome `marker_split`.
- The command exits 0.
- Marker evidence is passed to marker-based PR emission.
- Invalid, missing, stale, or malformed marker plans remain correctness stops.

### 7. Functional eval

Run the full suite with eval prerequisites installed:

```bash
bash tests/speckit-pro/run-all.sh --all
```

Expected outcome:

- The Layer 3 functional eval for a valid oversized spec shows autopilot continuing through reviewability sizing and emitting scoped PR evidence from the persisted marker plan.

### 8. Default verification

Before PR handoff, run:

```bash
bash tests/speckit-pro/run-all.sh
```

Expected outcome:

- Default deterministic layers pass.
- PR packet evidence includes review order, scope budget, traceability, verification, known gaps, rollback or flag notes, and rendered marker warnings.

# Phase 0 Research: PRSG-008 Layer Planner

## Decision: Implement the planner as one Bash script using `jq` for JSON

**Rationale**: The repository already validates shell scripts and standardizes
on Bash plus `jq` for plugin automation. This keeps the implementation inside
the existing Layer 4 test harness without adding runtime dependencies.

**Alternatives considered**: A Python helper would simplify parsing but add a
second runtime to the shipped plugin. Pure `sed`/`awk` JSON generation was
rejected because the constitution requires clear `jq` JSON manipulation instead
of brittle text hacks.

## Decision: Use one versioned JSON envelope for every outcome

**Rationale**: A single envelope with `tool`, `contract_version`, `status`,
`feature_dir`, `tasks_file`, `increments`, `warnings`, `errors`, and `summary`
lets callers handle success, invalid plans, and input errors with the same
shape. The closed status enum maps directly to exit codes `0`, `1`, and `2`.

**Alternatives considered**: Separate success and error schemas would be smaller
per response but harder for PRSG-009 and autopilot to consume safely. Stderr-only
failures were rejected because they are not fixture-testable.

## Decision: Treat the explicit dependency sections as authoritative

**Rationale**: `## Dependencies & Execution Order` and
`### Incremental Delivery` are written specifically to define order. The planner
can validate task sections against those declarations instead of inferring
delivery order from nearby prose.

**Alternatives considered**: Task order only was rejected because it ignores the
authoritative planning sections. File-overlap inference was rejected as brittle
and outside the planner-only scope.

## Decision: Fail malformed plans with structured diagnostics

**Rationale**: `missing_required_heading`, `empty_increment`,
`unknown_increment`, `dependency_cycle`, `contradictory_increment_order`,
`duplicate_increment_id`, `duplicate_task_id`, and `malformed_task` cover the
invalid-plan cases called out by the spec and keep failures repairable.

**Alternatives considered**: Best-effort partial plans were rejected because
bad task decompositions would flow into implementation and future stacked PR
emission. Falling back to one increment would hide split-plan defects.

## Decision: Preserve task metadata instead of inventing planner-only work

**Rationale**: Each task keeps its ID, title, checkbox-derived `todo` or `done`
status, `[P]` parallel flag, source line, file references, and test references.
`[P]` remains metadata and never becomes a separate increment.

**Alternatives considered**: Flattening parallel work loses useful coordination
metadata. Splitting parallel tasks into separate increments creates too many
review slices and changes the meaning of the task file.

## Decision: Report missing references as warnings

**Rationale**: Some coordination or review tasks legitimately lack direct file
or test paths, while broken paths should stay visible to maintainers. The
warning codes `task_without_references` and `reference_not_found` preserve that
signal without blocking otherwise valid plans.

**Alternatives considered**: Failing all missing references was too strict for
non-code tasks. Inferring paths from neighboring tasks was rejected because it
would create unreviewable ownership guesses.

## Decision: Keep size metadata counts-only

**Rationale**: PRSG-008 only needs advisory shape data for future PR splitting:
task count, file-reference count, distinct-file count, test-reference count, and
distinct-test count. LOC hints, thresholds, verdicts, and PRSG-006 semantics
belong outside this planner.

**Alternatives considered**: Adding budget verdicts was rejected as scope creep.
Omitting size data entirely was rejected because PRSG-009 needs lightweight
slice-shape metadata.

## Decision: Wire autopilot after PRSG-007 route recording

**Rationale**: PRSG-007 decides whether split planning is relevant. PRSG-008
parses layer plans only when the recorded route is `split-PR`, then stops before
implementation if the planner returns `invalid_plan` or `input_error`.

**Alternatives considered**: Calling the route script from `plan-layers.sh` was
rejected because it would couple two independently testable scripts. Always
running the planner was rejected because non-split routes do not require a layer
plan.

# Data Model: PRSG-008 Layer Planner

## LayerPlan

Represents one planner result for a feature directory.

Fields:

- `tool`: Stable tool identifier, `plan-layers`.
- `contract_version`: Planner contract version, starting at `1`.
- `status`: One of `ok`, `invalid_plan`, or `input_error`.
- `feature_dir`: Repo-relative feature directory path when available.
- `tasks_file`: Repo-relative `tasks.md` path when available.
- `increments`: Ordered array of `Increment` objects. Empty for input errors.
- `warnings`: Array of warning `Diagnostic` objects.
- `errors`: Array of error `Diagnostic` objects.
- `summary`: Counts and status text for humans and callers.

Validation rules:

- `status=ok` maps to exit `0` and may include warnings.
- `status=invalid_plan` maps to exit `1` and must include at least one error.
- `status=input_error` maps to exit `2` and must include at least one error.
- The envelope shape is stable for every status.

## Increment

Represents an ordered semantic delivery unit parsed from `tasks.md`.

Fields:

- `id`: Stable semantic ID such as `foundation`, `us1`, `us2`, or `polish`.
- `name`: Human-readable increment name from the task heading or delivery list.
- `kind`: One of `foundation`, `story`, or `polish`.
- `order`: Zero-based execution order.
- `depends_on`: Array of increment IDs that must precede this increment.
- `source`: Source heading and line metadata.
- `tasks`: Embedded ordered `Task` objects.
- `files`: Distinct repo-relative file references from tasks in this increment.
- `tests`: Distinct repo-relative test references from tasks in this increment.
- `advisory_size`: Counts-only metadata.

Validation rules:

- `id` must match `foundation`, `polish`, or `us<N>` where `<N>` is a positive
  decimal integer with no leading zeroes.
- Every declared increment must contain at least one parseable checkbox task.
- Duplicate semantic increment IDs fail with `duplicate_increment_id`.
- Unknown dependencies fail with `unknown_increment`.
- Cycles fail with `dependency_cycle`.
- Task order must not contradict declared incremental order.

## Task

Represents one checkbox task parsed from an increment section.

Fields:

- `id`: Task identifier from `tasks.md`.
- `title`: Task title without checkbox syntax or `[P]`.
- `story`: Story ID such as `us1`, or `null` for foundation/polish work.
- `increment_id`: Parent increment ID.
- `status`: `todo` for unchecked tasks, `done` for checked tasks.
- `parallel`: Boolean derived from `[P]`.
- `source`: Source file and line metadata.
- `files`: Repo-relative file references extracted from task text.
- `tests`: Repo-relative test references extracted from task text.

Validation rules:

- `story`, when present, must match the `us<N>` grammar; `increment_id` must
  match the semantic increment ID grammar.
- Duplicate task IDs fail with `duplicate_task_id`.
- Checkbox task-like lines inside increment sections must match the supported
  grammar; malformed lines fail with `malformed_task`.
- Tasks with no file or test references emit `task_without_references` warnings.
- Missing referenced paths emit `reference_not_found` warnings with `kind` set
  to `file` or `test`.

## Diagnostic

Represents a warning or error with one shared shape.

Fields:

- `code`: Stable diagnostic code.
- `severity`: `warning` or `error`.
- `message`: Concise human-readable message.
- `source`: File and line metadata when available.
- `details`: Machine-readable context.

Validation rules:

- Error codes are limited to `missing_required_heading`, `empty_increment`,
  `unknown_increment`, `dependency_cycle`, `contradictory_increment_order`,
  `duplicate_increment_id`, `duplicate_task_id`, `malformed_task`,
  `invalid_invocation`, `feature_dir_not_found`, `feature_dir_unreadable`,
  `tasks_file_missing`, and `tasks_file_unreadable`.
- Warning codes are limited to `task_without_references` and
  `reference_not_found`.
- Invalid-plan and input-error codes must use severity `error`; warning codes
  must use severity `warning`.
- `reference_not_found.details.kind` must be `file` or `test`.
- Per-code `details` payloads are closed and fixture-testable:
  `missing_required_heading` requires `required_heading`; `empty_increment` and
  `unknown_increment` require `increment_id`; `dependency_cycle` requires
  `cycle`; `contradictory_increment_order` requires `expected_order` and
  `observed_order`; `duplicate_increment_id` requires `increment_id`,
  `first_source`, and `duplicate_source`; `duplicate_task_id` requires
  `task_id`, `first_source`, and `duplicate_source`; `malformed_task` requires
  `line_text`; `task_without_references` requires `task_id` and
  `increment_id`; `reference_not_found` requires `kind`, `reference`, and
  `task_id`; `invalid_invocation` requires `expected_args` and
  `received_args`; `feature_dir_not_found` and `feature_dir_unreadable`
  require `feature_dir`; `tasks_file_missing` and `tasks_file_unreadable`
  require `tasks_file`.

## AutopilotLayerPlanState

Represents the autopilot-owned persistence of a successful planner result.

Fields:

- `route`: PRSG-007 route value.
- `layer_plan`: Full `LayerPlan` envelope returned by the planner.
- `workflow_summary`: Concise summary written to the workflow `## Layer Plan`
  section.
- `warnings`: Planner warnings carried forward into implementation context.

State transitions:

- `route=split-PR` and planner exit `0`: persist `layer_plan`, record workflow
  summary, and continue.
- `route=split-PR` and planner exit `1`: stop before implementation with the
  fixed invalid-plan message and diagnostics.
- `route=split-PR` and planner exit `2`: stop before implementation with an
  input-error message and diagnostics.
- Any other route: skip layer planning and continue with route context.

# Contract: `plan-layers.sh` Output

## Command

```bash
speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh <feature-dir>
```

The command accepts exactly one feature directory and resolves
`<feature-dir>/tasks.md`. It is read-only: it writes JSON to stdout, concise
human summaries to stderr, and no repository files.

## Exit Codes

| Exit | Status | Meaning |
|------|--------|---------|
| 0 | `ok` | A deterministic layer plan was emitted. Warnings may be present. |
| 1 | `invalid_plan` | `tasks.md` exists but violates the layer-plan contract. |
| 2 | `input_error` | Invocation, feature directory, or `tasks.md` input is missing or unreadable. |

## Envelope

Every outcome emits one JSON object with these top-level fields:

- `tool`: `plan-layers`
- `contract_version`: integer, starting at `1`
- `status`: `ok`, `invalid_plan`, or `input_error`
- `feature_dir`: repo-relative feature directory path when available
- `tasks_file`: repo-relative `tasks.md` path when available
- `increments`: ordered increment objects
- `warnings`: warning diagnostics
- `errors`: error diagnostics
- `summary`: counts and concise result text

## Status Invariants

- `status=ok` maps to exit `0`; `errors` MUST be empty, `warnings` MAY be
  present, and `increments` MUST contain at least one planned increment.
- `status=invalid_plan` maps to exit `1`; `errors` MUST contain at least one
  invalid-plan diagnostic for a readable `tasks.md` that violates this contract.
- `status=input_error` maps to exit `2`; `errors` MUST contain at least one
  input-error diagnostic and `increments` MUST be empty because no valid task
  plan was available to parse.

## Increment Object

Each increment includes:

- `id`: semantic ID such as `foundation`, `us1`, `us2`, or `polish`
- `name`: human-readable name
- `kind`: `foundation`, `story`, or `polish`
- `order`: zero-based order
- `depends_on`: prior increment IDs
- `source`: `{ "path": "...", "line": 12, "heading": "..." }`
- `tasks`: embedded task objects
- `files`: distinct repo-relative file references
- `tests`: distinct repo-relative test references
- `advisory_size`: counts only

`id` and `depends_on[]` values must match the PRSG-008 v1 semantic increment
ID grammar: `foundation`, `polish`, or `us<N>` where `<N>` is a positive
decimal integer with no leading zeroes.

`advisory_size` contains:

- `task_count`
- `file_reference_count`
- `distinct_file_count`
- `test_reference_count`
- `distinct_test_count`

It must not contain LOC hints, thresholds, reviewability verdicts, or PRSG-006
budget semantics.

## Task Object

Each task includes:

- `id`
- `title`
- `story`: `null` or a `us<N>` story ID
- `increment_id`: semantic increment ID matching the increment ID grammar
- `status`: `todo` or `done`
- `parallel`: boolean derived from `[P]`
- `source`
- `files`
- `tests`

## Diagnostics

Warnings and errors use one shared shape:

- `code`
- `severity`
- `message`
- `source`
- `details`

Invalid-plan error codes:

- `missing_required_heading`
- `empty_increment`
- `unknown_increment`
- `dependency_cycle`
- `contradictory_increment_order`
- `duplicate_increment_id`
- `duplicate_task_id`
- `malformed_task`

Input-error codes:

- `invalid_invocation`
- `feature_dir_not_found`
- `feature_dir_unreadable`
- `tasks_file_missing`
- `tasks_file_unreadable`

Warning codes:

- `task_without_references`
- `reference_not_found`

`reference_not_found.details.kind` is `file` or `test`.

Diagnostic `severity` is tied to code class: invalid-plan and input-error codes
use `error`, while warning codes use `warning`.

Diagnostic `details` is machine-readable and closed per code:

| Code | Required `details` keys |
|------|--------------------------|
| `missing_required_heading` | `required_heading` |
| `empty_increment` | `increment_id` |
| `unknown_increment` | `increment_id` |
| `dependency_cycle` | `cycle` |
| `contradictory_increment_order` | `expected_order`, `observed_order` |
| `duplicate_increment_id` | `increment_id`, `first_source`, `duplicate_source` |
| `duplicate_task_id` | `task_id`, `first_source`, `duplicate_source` |
| `malformed_task` | `line_text` |
| `task_without_references` | `task_id`, `increment_id` |
| `reference_not_found` | `kind`, `reference`, `task_id` |
| `invalid_invocation` | `expected_args`, `received_args` |
| `feature_dir_not_found` | `feature_dir` |
| `feature_dir_unreadable` | `feature_dir` |
| `tasks_file_missing` | `tasks_file` |
| `tasks_file_unreadable` | `tasks_file` |

## PRSG-009 Non-goals

PRSG-008 only emits a read-only layer plan. It MUST NOT create branches, write
PR bodies, restack changes, push commits, or emit stacked-PR topology. PRSG-009
owns branch creation, PR body generation, restacking, and multi-PR emission.

## Example Success Shape

```json
{
  "tool": "plan-layers",
  "contract_version": 1,
  "status": "ok",
  "feature_dir": "specs/prsg-008-layer-planner",
  "tasks_file": "specs/prsg-008-layer-planner/tasks.md",
  "increments": [
    {
      "id": "foundation",
      "name": "Foundation",
      "kind": "foundation",
      "order": 0,
      "depends_on": [],
      "source": {
        "path": "specs/prsg-008-layer-planner/tasks.md",
        "line": 42,
        "heading": "## Phase 1: Foundation"
      },
      "tasks": [
        {
          "id": "T001",
          "title": "Create planner script",
          "story": null,
          "increment_id": "foundation",
          "status": "todo",
          "parallel": false,
          "source": {
            "path": "specs/prsg-008-layer-planner/tasks.md",
            "line": 45
          },
          "files": [
            "speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh"
          ],
          "tests": [
            "tests/speckit-pro/layer4-scripts/test-plan-layers.sh"
          ]
        }
      ],
      "files": [
        "speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh"
      ],
      "tests": [
        "tests/speckit-pro/layer4-scripts/test-plan-layers.sh"
      ],
      "advisory_size": {
        "task_count": 1,
        "file_reference_count": 1,
        "distinct_file_count": 1,
        "test_reference_count": 1,
        "distinct_test_count": 1
      }
    }
  ],
  "warnings": [],
  "errors": [],
  "summary": {
    "increment_count": 1,
    "task_count": 1,
    "warning_count": 0,
    "error_count": 0,
    "message": "Planned 1 increment with 1 task."
  }
}
```

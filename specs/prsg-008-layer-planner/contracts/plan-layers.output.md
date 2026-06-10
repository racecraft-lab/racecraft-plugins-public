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
- `story`
- `increment_id`
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

Warning codes:

- `task_without_references`
- `reference_not_found`

`reference_not_found.details.kind` is `file` or `test`.

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

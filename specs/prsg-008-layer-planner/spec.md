# Feature Specification: Layer-planner - PRSG-008

**Feature Branch**: `prsg-008-layer-planner`

**Created**: 2026-06-09

**Status**: Draft

**Input**: User description: "Phase 4 needs a read-only layer planner that turns a feature directory's tasks.md into a deterministic JSON layer plan before PRSG-009 emits stacked PRs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Emit a Stable Layer Plan (Priority: P1)

As `speckit-autopilot`, I need to pass a feature directory to the planner and receive a stable layer plan on stdout so implementation can proceed with an explicit increment order when split planning is relevant.

**Why this priority**: This is the minimum useful feature. Without a deterministic layer plan, Phase 4 cannot hand PRSG-009 an executable decomposition.

**Independent Test**: Can be fully tested by running the planner against a fixture feature directory with a valid `tasks.md` and comparing stdout to an approved JSON plan while confirming the fixture directory is unchanged.

**Acceptance Scenarios**:

1. **Given** a feature directory with a valid `tasks.md`, **When** the planner is run with that directory, **Then** it exits successfully and emits one deterministic JSON layer plan to stdout.
2. **Given** the same valid `tasks.md` is planned repeatedly, **When** the planner is run multiple times, **Then** the emitted JSON is byte-for-byte stable except for no runtime-dependent fields.
3. **Given** the planner runs successfully, **When** the feature directory is inspected afterward, **Then** no repository files are created, modified, moved, or deleted.

---

### User Story 2 - Parse Ordered Increments from Tasks (Priority: P1)

As PRSG-009, I need Foundation, user-story, and Polish work grouped into ordered semantic increments so stacked PRs can be emitted in dependency order later.

**Why this priority**: PRSG-009 depends on an ordered, machine-readable contract rather than ad hoc task parsing.

**Independent Test**: Can be tested by using task fixtures that contain `## Dependencies & Execution Order`, `### Incremental Delivery`, Foundation, user-story phases, and Polish sections, then verifying the expected increment IDs and task memberships.

**Acceptance Scenarios**:

1. **Given** `tasks.md` declares dependency order and incremental delivery order, **When** the planner parses it, **Then** those explicit sections determine the increment order.
2. **Given** task sections include Foundation, user-story phases, and Polish, **When** the planner emits the layer plan, **Then** increment IDs use semantic names such as `foundation`, `us1`, `us2`, and `polish`.
3. **Given** a task is marked parallel with `[P]`, **When** the planner emits that task, **Then** `[P]` is preserved as task metadata and does not become its own increment.

---

### User Story 3 - Diagnose Malformed Plans (Priority: P2)

As a maintainer, I need malformed task decompositions to fail with structured diagnostics so I can repair the task file without guessing what the planner rejected.

**Why this priority**: Reliable diagnostics prevent silent bad plans and make fixture failures reviewable.

**Independent Test**: Can be tested with malformed fixtures that violate declared ordering, omit required planning sections, duplicate increment identifiers, or reference unknown increments.

**Acceptance Scenarios**:

1. **Given** `tasks.md` has contradictory increment ordering, **When** the planner runs, **Then** it exits with an invalid-plan status and emits structured JSON error details to stdout.
2. **Given** the planner rejects a malformed plan, **When** the maintainer reads stderr, **Then** they see a concise human-readable summary of the failure.
3. **Given** a task references a missing file or test path, **When** the rest of the plan is valid, **Then** the planner succeeds and reports the missing reference as a warning, not a failure.

---

### User Story 4 - Gate Autopilot Before Implementation (Priority: P2)

As `speckit-autopilot`, I need the planner to run after PRSG-007 route recording and before implementation so split-relevant specs cannot proceed with an invalid layer plan.

**Why this priority**: The planner only creates value when it is inserted at the correct point in the Phase 4 flow.

**Independent Test**: Can be tested by using autopilot fixtures where routing marks split planning as relevant and verifying implementation does not begin until the planner succeeds.

**Acceptance Scenarios**:

1. **Given** PRSG-007 records split planning as relevant, **When** autopilot reaches the implementation handoff, **Then** it runs the layer planner before starting implementation work.
2. **Given** the layer planner returns an invalid-plan or usage/input error, **When** autopilot receives that result, **Then** it stops before implementation and surfaces the planner diagnostics.
3. **Given** PRSG-007 records split planning as not relevant, **When** autopilot reaches implementation, **Then** no layer plan is required for implementation to continue.

### Edge Cases

- The supplied feature directory does not exist, is not readable, or does not contain `tasks.md`.
- `tasks.md` is present but omits the explicit dependency or incremental delivery sections needed for authoritative ordering.
- The declared increment order references an increment that has no matching task section.
- A declared or present increment section contains no parseable checkbox tasks.
- The task order contradicts the declared dependency or incremental delivery order.
- Multiple sections map to the same semantic increment ID.
- Multiple checkbox tasks use the same task identifier.
- Tasks are checked, unchecked, or partially completed before planning.
- Tasks include `[P]`, file references, test references, or no references at all.
- File or test references appear to be missing even though the task plan is otherwise valid.
- Additional task prose appears between supported sections.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The planner MUST accept exactly one feature directory argument and read `tasks.md` from that directory.
- **FR-002**: The planner MUST treat missing, unreadable, or invalid input paths as usage/input errors.
- **FR-003**: The planner MUST emit successful layer plans as stable JSON to stdout.
- **FR-004**: The planner MUST emit concise human-readable diagnostic summaries to stderr when warnings or errors are present.
- **FR-005**: The planner MUST be read-only and MUST NOT create, modify, move, or delete repository files.
- **FR-006**: The planner MUST parse Foundation, user-story, and Polish work into ordered increments when those phases are present in `tasks.md`.
- **FR-007**: The planner MUST use `## Dependencies & Execution Order` and `### Incremental Delivery` as the authoritative sources for increment ordering.
- **FR-008**: The planner MUST validate the authoritative increment order against the order and membership of tasks in `tasks.md`.
- **FR-009**: The planner MUST fail plans that are missing required ordering information, contain empty declared increments, contain contradictory ordering, duplicate semantic increment IDs, duplicate task IDs, malformed checkbox tasks, or reference unknown increments.
- **FR-010**: The planner MUST use semantic increment IDs, including `foundation`, `us1`, `us2`, and `polish` where applicable.
- **FR-010a**: Semantic increment IDs MUST match the PRSG-008 v1 grammar `foundation`, `polish`, or `us<N>` where `<N>` is a positive decimal integer with no leading zeroes. No other increment ID values are valid in planner output.
- **FR-011**: The planner MUST preserve each planned task's identifier, title, checkbox state, source line number, parallel marker state, and declared file or test references when present.
- **FR-012**: The planner MUST preserve `[P]` as task metadata and MUST NOT create a separate parallel-work increment from it.
- **FR-013**: The planner MUST report missing file or test references as warnings without failing an otherwise valid plan.
- **FR-014**: The planner MUST define and publish a schema-backed output contract for successful plans, warnings, and structured errors.
- **FR-014a**: The planner JSON MUST use one versioned top-level envelope for every outcome: `tool`, `contract_version`, `status`, `feature_dir`, `tasks_file`, `increments`, `warnings`, `errors`, and `summary`.
- **FR-014b**: The `status` field MUST use the closed enum `ok`, `invalid_plan`, or `input_error`, mapping to exit codes `0`, `1`, and `2` respectively.
- **FR-014c**: Each increment object MUST include `id`, `name`, `kind`, `order`, `depends_on`, `source`, embedded `tasks`, `files`, `tests`, and `advisory_size`.
- **FR-014d**: Each task object MUST include `id`, `title`, `story`, `increment_id`, `status`, `parallel`, `source`, `files`, and `tests`; task `status` MUST use `todo` for unchecked tasks and `done` for checked tasks.
- **FR-014e**: Warnings and errors MUST use the same diagnostic shape: `code`, `severity`, `message`, `source`, and `details`.
- **FR-014f**: Advisory size metadata MUST be counts-only in PRSG-008 v1: task count, file-reference count, distinct-file count, test-reference count, and distinct-test count. The planner MUST NOT emit LOC hints, budget verdicts, thresholds, or PRSG-006 reviewability-gate semantics.
- **FR-014g**: Invalid-plan diagnostic codes MUST be drawn from `missing_required_heading`, `empty_increment`, `unknown_increment`, `dependency_cycle`, `contradictory_increment_order`, `duplicate_increment_id`, `duplicate_task_id`, and `malformed_task`.
- **FR-014h**: Warning diagnostic codes MUST be drawn from `task_without_references` and `reference_not_found`; `reference_not_found` details MUST identify `kind` as `file` or `test`.
- **FR-014i**: A valid `tasks.md` MUST include both `## Dependencies & Execution Order` and `### Incremental Delivery`; missing either heading is `missing_required_heading`, status `invalid_plan`, exit `1`.
- **FR-014j**: Inside increment sections, checkbox task-like lines MUST match the supported task grammar with task ID, checkbox state, optional `[P]`, and title. Non-task prose and non-task bullets MAY be ignored, but malformed task-like lines MUST fail as `malformed_task`.
- **FR-014k**: Input-error diagnostic codes MUST be drawn from `invalid_invocation`, `feature_dir_not_found`, `feature_dir_unreadable`, `tasks_file_missing`, and `tasks_file_unreadable`; these codes MUST use status `input_error`, severity `error`, and exit code `2`.
- **FR-014l**: Each diagnostic code MUST define a machine-readable `details` payload with stable required keys so fixtures and downstream callers never need to parse the human-readable `message` field. Required `details` keys are: `required_heading` for `missing_required_heading`; `increment_id` for `empty_increment` and `unknown_increment`; `cycle` for `dependency_cycle`; `expected_order` and `observed_order` for `contradictory_increment_order`; `increment_id`, `first_source`, and `duplicate_source` for `duplicate_increment_id`; `task_id`, `first_source`, and `duplicate_source` for `duplicate_task_id`; `line_text` for `malformed_task`; `task_id` and `increment_id` for `task_without_references`; `kind`, `reference`, and `task_id` for `reference_not_found`; `expected_args` and `received_args` for `invalid_invocation`; `feature_dir` for `feature_dir_not_found` and `feature_dir_unreadable`; and `tasks_file` for `tasks_file_missing` and `tasks_file_unreadable`.
- **FR-014m**: Diagnostic `code` and `severity` values MUST be schema-consistent: invalid-plan and input-error codes MUST use severity `error`, and warning codes MUST use severity `warning`.
- **FR-014n**: Dependency DAG output MUST be deterministic: each `depends_on` array MUST contain only unique semantic increment IDs that precede the increment in the authoritative execution order and MUST be emitted in that authoritative order; `dependency_cycle.details.cycle` MUST report one stable cycle path selected by the first affected increment in the authoritative order, with cycle members emitted in traversal order starting at that increment.
- **FR-014o**: Supported checkbox markers in task-like lines are `[ ]`, `[x]`, and `[X]`; `[ ]` MUST map to task status `todo`, and `[x]` or `[X]` MUST map to task status `done`. Any other task-like bracket state in an increment section, including partial-state markers such as `[-]`, `[~]`, or `[?]`, MUST fail as `malformed_task` so the output status enum remains only `todo` or `done`.
- **FR-014p**: Planner path fields MUST be normalized relative to the current Git worktree root: `feature_dir`, `tasks_file`, every `source.path`, and all `files` and `tests` references MUST be emitted without absolute prefixes, leading `./`, or redundant `.` segments. Duplicate file/test references after normalization MUST contribute once to each affected `files` or `tests` array, with arrays emitted in `LC_ALL=C` lexical order. References that normalize outside the worktree root MUST NOT be emitted as repo-relative paths and MUST produce a `reference_not_found` warning that preserves the original reference string.
- **FR-015**: The planner MUST use exit code `0` for successful plans, `1` for invalid plans, and `2` for usage or input errors.
- **FR-016**: The planner MUST remain independent from PRSG-007 routing logic and MUST NOT reclassify whether split planning is relevant.
- **FR-017**: `speckit-autopilot` MUST run the planner immediately after PRSG-007 route recording after G5 and before Analyze when the recorded route is exactly `split-PR`.
- **FR-017a**: `speckit-autopilot` MUST NOT require a layer plan for `one-navigable-PR`, `branch-by-abstraction`, `single-atomic-PR`, or `out-of-scope` routes, while preserving PRSG-007 releasability warnings as context.
- **FR-017b**: On a successful planner run, `speckit-autopilot` MUST persist the full versioned layer-plan envelope in `autopilot-state.json`, record a concise summary in the workflow `## Layer Plan` section, and pass only the relevant increment context to implementation prompts.
- **FR-018**: `speckit-autopilot` MUST stop before implementation and surface planner diagnostics when planner validation fails.
- **FR-018a**: When the planner returns exit `1`, autopilot MUST emit this fixed stop line before diagnostics: `STOP: Layer planner returned invalid_plan (exit 1) for <feature-dir>; implementation has not started. Fix tasks.md using the planner diagnostics below, then rerun autopilot from the Layer Plan step.`
- **FR-018b**: When the planner returns exit `2`, autopilot MUST stop before implementation with a distinct `input_error` message and include the planner diagnostics.
- **FR-018c**: When the planner returns exit `0` with warnings, autopilot MUST continue and carry those warnings into the workflow/state implementation context.
- **FR-019**: The feature MUST remain planner-only and MUST NOT create branches, generate PR bodies, restack changes, or emit multi-PR topology.
- **FR-020**: The planner contract MUST be deterministic and fixture-testable across valid, warning, invalid-plan, and usage/input cases.

### Reviewability Budget *(mandatory)*

- **Primary surface**: harness/adapter
- **Secondary surfaces, if any**: docs/process
- **Projected reviewable LOC**: approximately 350 production LOC, excluding fixtures and generated artifacts
- **Projected production files**: 3 runtime/prose surfaces (`plan-layers.sh`, Claude autopilot prose, Codex autopilot prose)
- **Projected total files**: approximately 14-16, mostly contract, test, and fixture files that are intentional contract coverage and excluded from production reviewable LOC
- **Budget result**: within budget
- **Split decision**: This remains one spec because PRSG-008 is limited to a read-only planner contract and autopilot handoff. Branch creation, PR body generation, restacking, and stacked PR emission remain deferred to PRSG-009.

### PR Review Packet Requirements *(mandatory)*

- PR description MUST include: what changed, why, non-goals, review order, scope budget, traceability, verification evidence, known gaps, and rollback or feature-flag notes.
- Traceability MUST map each major requirement or success criterion to changed files and verification evidence.
- Deferred work MUST name PRSG-009 for stacked PR emission and any follow-up issue or spec for behavior intentionally excluded from PRSG-008.

### Key Entities *(include if feature involves data)*

- **Layer Plan**: The complete planner result for a feature directory, emitted as a versioned JSON envelope with `status`, input paths, ordered increments, warnings, errors, and a summary.
- **Increment**: A semantic delivery unit such as `foundation`, `us1`, `us2`, or `polish`, with dependency order, source context, embedded tasks, aggregate file/test references, and counts-only advisory size metadata.
- **Task Reference**: A task extracted from `tasks.md`, including task ID, title, story, semantic increment ID, checkbox-derived `todo` or `done` status, source line number, parallel marker state, and declared file or test references.
- **Diagnostic**: A structured warning or error with a stable code, `warning` or `error` severity, concise message, source context, and machine-readable details.
- **Planner Invocation**: The read-only request to plan one feature directory, including success, invalid-plan, and usage/input outcomes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a valid fixture, five consecutive planner runs produce identical JSON output.
- **SC-002**: For task files with up to 200 tasks, maintainers receive a complete layer plan in under 1 second on a typical development machine.
- **SC-003**: 100% of malformed-plan fixtures return exit code `1`, structured JSON error output, and a concise stderr summary.
- **SC-004**: 100% of usage/input fixtures return exit code `2`, structured JSON error output, and no repository file changes.
- **SC-005**: 100% of valid fixtures with missing file or test references return exit code `0` with warning diagnostics.
- **SC-006**: For every task in a valid layer plan, reviewers can trace the emitted task back to its source line and checkbox state in `tasks.md`.
- **SC-007**: When split planning is relevant and planner validation fails, autopilot never starts implementation work.
- **SC-008**: The PRSG-008 review packet names PRSG-009 as the owner of branch, PR body, restacking, and multi-PR emission work.

## Assumptions

- `tasks.md` follows the existing SpecKit task-list structure closely enough for headings, checkboxes, task IDs, and user-story labels to be recognized.
- Explicit dependency and incremental delivery sections are the source of truth when task prose could imply a different ordering.
- PRSG-007 has already recorded whether split planning is relevant before autopilot considers running the planner.
- Only PRSG-007's `split-PR` route requires a layer-plan handoff in PRSG-008.
- Missing file and test references can be identified from references already written in task text; the planner does not infer ownership from neighboring tasks.
- The output schema is versioned with the planner contract so PRSG-009 can consume it without guessing field meanings.
- Counts-only advisory size metadata is enough for PRSG-009 to reason about slice shape; PRSG-006 remains the owner of LOC estimation and budget verdicts.
- PRSG-009 will own branch creation, PR body generation, restacking, and stacked PR emission.

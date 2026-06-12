# Data Model: Non-Stopping Reviewability Markers

## Entity: Reviewability Finding

Represents one parseable sizing result from a task or final reviewability check.

**Fields**
- `status`: `pass`, `warn`, `exception`, `block`, or `not_estimated`.
- `mode`: Gate mode, such as `tasks` or `final`.
- `scope`: Feature, marker, story, or full-diff scope that was measured.
- `reason`: Human-readable reason emitted by the gate.
- `metrics`: Object containing reviewable LOC, production file count, total file count, primary surface count, and any threshold values.
- `evidence_path`: Repo-relative path to captured gate evidence, when persisted.
- `source`: `post_g5`, `final_backstop`, `marker_estimate`, or `manual_exception`.
- `is_marker_input`: Boolean. True for parseable size-only findings that should shape markers.
- `is_correctness_block`: Boolean. True only when the finding is malformed, unsafe, unreadable, stale, or not tied to the current feature.

**Validation Rules**
- `status=block` is marker input only when the JSON is valid, the mode is expected, the block is size-only, and correctness evidence remains valid.
- Missing status, missing mode, invalid JSON, unreadable evidence, or stale feature linkage is correctness-blocking.

## Entity: PR Marker Plan

Top-level durable marker state stored as `pr_marker_plan` in `autopilot-state.json` and mirrored into workflow evidence.

**Fields**
- `schema_version`: `pr-marker-plan.v1`.
- `kind`: `pr_marker_plan`.
- `feature_id`: Current feature/spec ID.
- `status`: `planned`, `checkpointing`, `emission_ready`, `emitted`, `collapsed`, `stale`, or `invalid`.
- `source_fingerprint`: Fingerprint object tying markers to the current spec, plan-declared file/test scope, tasks, reviewability finding, and hazard decision.
- `markers`: Ordered array of PR Marker entities.
- `warnings`: Structured warnings at plan scope.
- `created_at` / `updated_at`: ISO-8601 timestamps.

**Relationships**
- Owns many PR Markers.
- Consumes Reviewability Findings and Atomicity Route output.
- Produces Marker Evidence and Emission Packets.

**Validation Rules**
- `markers[]` order and one-based `review_order` must agree.
- `source_fingerprint` must match the current feature inputs on resume and final emission, including plan-declared file/test scope.
- Missing, malformed, stale, or fingerprint-mismatched marker plans are correctness stops at final emission.
- Workflow evidence must mirror the same schema version, source fingerprint, ordered marker IDs, review order, warnings, checkpoints, and emission mappings as `autopilot-state.json`.

## Entity: PR Marker

One planned review scope.

**Fields**
- `id`: `foundation`, `us<N>`, `us<N>-part<M>`, or `full-spec`.
- `review_order`: One-based integer.
- `kind`: `foundation`, `user_story`, `user_story_part`, or `full_spec`.
- `parent_marker_id`: `null` for normal markers, or `us<N>` for subdivided `us<N>-part<M>` child markers.
- `source_boundary`: Source section, user story number, and first/last task IDs.
- `task_ids`: Ordered task IDs included in this marker.
- `folded_polish_task_ids`: Ordered Polish task IDs folded into this marker.
- `folded_polish_target_reason`: Structured explanation of why Polish tasks folded into this marker.
- `declared_files`: File operations declared for the marker.
- `declared_tests`: Tests declared for the marker.
- `reviewability`: Marker-level Reviewability Finding.
- `hazards`: Hazard notes from atomicity or shared-mutation checks.
- `subdivision`: `none`, `safe_split`, `no_safe_boundary`, or `hazard_collapsed`, with details.
- `implementation_checkpoint`: Pending or completed checkpoint evidence.
- `emission_mapping`: Pending or emitted PR packet mapping.
- `warnings`: Structured marker warnings.

**Validation Rules**
- Marker IDs must be stable for unchanged source boundaries.
- `foundation` is present only when Foundation tasks exist.
- One marker exists per user story before safe subdivision.
- Safe subdivision replaces the parent `us<N>` marker with ordered `us<N>-part<M>` child markers for scoped emission; the parent marker is not emitted separately.
- Polish cannot create a cleanup-only marker; it must fold into the nearest preceding eligible non-Polish marker, or the next eligible non-Polish marker when no preceding marker owns the dependency and declared file/test scope.
- `full-spec` appears only as the hazard-collapsed emission marker.
- Existing checkpoint and emission evidence can be preserved on resume only when marker ID, source boundary, task IDs, folded Polish task IDs, and source fingerprint still match.

## Entity: Safe Task Cluster

A candidate in-story subdivision.

**Fields**
- `story_id`: User story number.
- `task_ids`: Contiguous ordered task IDs.
- `start_task_id` / `end_task_id`: Boundary task IDs.
- `dependency_edges`: Edges inspected for boundary crossing.
- `declared_files`: Complete file declarations for the cluster.
- `declared_tests`: Complete test declarations for the cluster.
- `hazard_signals`: Shared mutation or release-safety signals.
- `is_safe`: Boolean.
- `rejection_reason`: Structured reason when unsafe.

**Validation Rules**
- Tasks must be contiguous inside the same user story.
- No dependency edge may cross the proposed boundary.
- Declared files and tests must be complete.
- Shared mutation or hazard signals reject the cluster.
- Original task order is preserved.

## Entity: Marker Evidence

Workflow/state evidence explaining marker planning and later implementation/emission outcomes.

**Fields**
- `marker_id`
- `schema_version`
- `source_fingerprint`
- `source_tasks`
- `review_order`
- `reviewability_status`
- `hazards`
- `verification`
- `final_backstop_status`
- `metrics`
- `evidence_path`
- `emitted_pr`
- `warnings`

**Validation Rules**
- Warnings use `code`, `severity`, `message`, `source`, and `details`.
- Evidence must be renderable into PR packet warnings.
- Evidence must link back to the marker plan fingerprint.
- Evidence must not maintain marker IDs, review order, warning objects, or emission mappings that differ from `autopilot-state.json`.

## Entity: Emission Packet

The final PR creation payload associated with one marker or one hazard-collapsed PR.

**Fields**
- `marker_id`: Marker ID, or `full-spec` for hazard collapse.
- `source_marker_ids`: Original marker IDs included in the packet.
- `title`
- `body`
- `review_order`
- `scope_budget`
- `traceability`
- `verification_evidence`
- `warnings`
- `rollback_or_flags`
- `pr_number` / `pr_url`: Populated after creation.

**Validation Rules**
- Non-hazard emission creates one packet per persisted marker in marker order.
- Hazard emission creates exactly one `full-spec` packet and maps back to all original marker checkpoints.
- Final full-diff size block plus valid current marker plan must use `marker_split`, exit 0, and pass marker evidence forward.

## State Transitions

```text
absent
  -> planned
  -> checkpointing
  -> emission_ready
  -> emitted

planned|checkpointing|emission_ready
  -> stale   when source_fingerprint no longer matches
  -> invalid when schema or required evidence is malformed
  -> collapsed when hazard route requires one emitted PR
```

Correctness stops occur at `stale` or `invalid`. Reviewability size warnings continue and remain attached as structured evidence.

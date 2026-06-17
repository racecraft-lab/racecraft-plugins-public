# TACD-001 Data Model

TACD-001 is a research spike, so this data model describes the structured
concepts the spike report must contain. It is not an application schema.

## Entity: Named-Tool Reference

Represents one source occurrence that names an optional research/context tool,
connector, MCP server, skill/plugin, or repo-local helper.

**Fields**:

- `source_path`: repository-relative file path
- `line_context`: exact line number or compact line range
- `reference_text`: the named tool, server, connector, or concrete runtime ID
- `surface_id`: associated Runtime Surface identifier
- `classification`: one Allowlist Category
- `rationale`: why the classification is correct
- `action_owner`: `TACD-001`, `TACD-002`, `TACD-003`, `TACD-004`, or `none`
- `rewrite_condition`: condition needed before a later rewrite, if any

**Validation rules**:

- Must include `source_path`, `line_context`, `classification`, and `rationale`.
- Generic MCP/app/installed-tool language is excluded unless tied to a concrete
  tool ID, vendor/server list, or prerequisite expectation.
- Generated payload findings must point back to source-derived duplicate status
  when applicable.

## Entity: Runtime Surface

Represents a source area that may influence Claude Code or Codex behavior,
messaging, dependency metadata, or expectations.

**Fields**:

- `surface_id`: stable label for the surface
- `runtime`: `Claude Code`, `Codex`, `shared`, or `generated`
- `surface_type`: `agent`, `skill`, `reference`, `script`, `metadata`, `docs`,
  `eval`, `test`, `generated_payload`, or `historical`
- `paths_checked`: repository-relative paths or globs
- `active_status`: `active`, `generated_duplicate`, `historical`,
  `fixture_only`, or `out_of_scope`
- `notes`: relevant evidence summary

**Validation rules**:

- The report must record checked surfaces even when no named-tool findings are
  found.
- Paths that contain both active guidance and historical notes must be
  classified at reference level.

## Entity: Capability Mechanics Evidence

Represents evidence for how a runtime discovers or uses capabilities without a
hardcoded vendor-specific list.

**Fields**:

- `runtime`: `Claude Code` or `Codex`
- `capability_class`: `installed_tools`, `mcp_app_connectors`,
  `skills_plugins`, or `repo_local_helpers`
- `evidence_state`: `source-backed`, `probe-backed`, `unsupported`,
  `unresolved`, or `environment-specific`
- `source_paths`: source files and line contexts, if source-backed
- `probe_ref`: Sanitized Probe Summary identifier, if probe-backed or
  environment-specific
- `conclusion`: reviewer-facing mechanics conclusion
- `confidence`: `high`, `medium`, or `low`
- `confidence_rationale`: one-sentence explanation for the confidence level
- `absent_capability_disposition`: documented fallback path, explicit
  unsupported state, explicit unresolved state, or downstream owner/reviewer
  decision needed when the capability is absent, unsupported, unavailable, or
  unverified

**Validation rules**:

- Each runtime/capability pair must appear in the runtime-by-capability matrix.
- Source-backed evidence must cite local repository paths and line contexts.
- Probe-backed evidence must not expose raw inventories or local identifiers.
- Unavailable or unsupported capabilities must be recorded as report evidence,
  not silently converted into implementation assumptions or behavior changes.

## Entity: Runtime-by-Capability Matrix Cell

Represents one cell in the platform mechanics matrix.

**Fields**:

- `runtime`
- `capability_class`
- `status`
- `evidence_refs`
- `reviewer_note`
- `confidence`: `high`, `medium`, or `low`
- `confidence_rationale`: one-sentence explanation following the confidence
  rubric
- `absent_capability_disposition`: documented fallback path, explicit
  unsupported state, explicit unresolved state, or downstream owner/reviewer
  decision needed

**Validation rules**:

- `status` must be one of `source-backed`, `probe-backed`, `unsupported`,
  `unresolved`, or `environment-specific`.
- A cell marked `unresolved` must explain what evidence is missing and which
  downstream spec or reviewer decision owns it.
- A cell marked `unsupported`, `unresolved`, or `environment-specific` must not
  imply implementation support unless cited source or sanitized probe evidence
  supports that conclusion.

## Entity: Sanitized Probe Summary

Represents a reproducible probe without committing sensitive or
machine-specific raw output.

**Fields**:

- `probe_id`
- `command_or_method`
- `purpose`
- `sanitized_observed_result`
- `excluded_raw_details`
- `evidence_state`
- `reviewer_conclusion`
- `reproduce_notes`

**Validation rules**:

- Must exclude raw runtime inventories, connector lists, session/request IDs,
  absolute machine paths, access tokens, usage/quota/cost fields, and full
  transcripts.
- Must preserve enough command/result detail for a reviewer to reproduce the
  mechanics or understand why the result is environment-specific.

## Entity: Directive-Home Recommendation

Represents the report's recommendation for where TACD-002 should place the
capability-discovery directive.

**Fields**:

- `recommended_home`: `shared_reference_with_pointers` or
  `runtime_specific_equivalents`
- `static_pointer_coverage`: summary of Claude and Codex pointer coverage
- `pointer_target_resolution`: how each runtime can resolve the pointer target
- `planned_eval_coverage`: functional eval scenarios TACD-004 should add
- `pass_fail_rationale`: why the recommended home passes or fails the proof bar
- `fallback_plan`: runtime-specific equivalent path if shared reference is not
  reliable

**Validation rules**:

- Shared reference plus pointers is valid only when both static pointer coverage
  and planned functional eval coverage are defined for Claude Code and Codex.
- If either runtime lacks evidence, recommend runtime-specific equivalents with
  a shared source-of-truth note.

## Entity: Allowlist Category

Represents an enforcement category TACD-004 can later turn into deterministic
checks.

**Fields**:

- `category_name`
- `allowed_status`: `block`, `allow`, or `review`
- `description`
- `example_surfaces`
- `tacd_owner`
- `false_positive_guard`

**Required category set**:

- active runtime guidance
- active runtime/dependency metadata
- prerequisite/user-facing messaging
- deterministic/eval expectation
- dependency metadata
- generated source-derived duplicate
- historical/provenance
- fixture/test-only
- ambiguous/requires-review
- explicitly out of scope

**Validation rules**:

- Historical/provenance and fixture-only categories must not be collapsed into
  active guidance.
- Active prose that recommends named optional tools must be separated from
  concrete runtime/dependency metadata.
- Ambiguous active-vs-historical references must use
  `ambiguous/requires-review` with `allowed_status: review`, low confidence,
  candidate categories, missing evidence, and an owner decision needed.

## Entity: Downstream Handoff

Represents later work identified by the report.

**Fields**:

- `target_spec`: `TACD-002`, `TACD-003`, or `TACD-004`
- `scope`
- `inputs_from_report`
- `non_goals`
- `validation_needed`

**Validation rules**:

- TACD-002 owns behavior-changing agent guidance.
- TACD-003 owns prerequisite and user-facing docs messaging.
- TACD-004 owns deterministic checks and functional eval expectations.

## Entity: Verification Evidence

Represents checks proving TACD-001 stayed within spike scope.

**Fields**:

- `check_name`
- `command`
- `expected_result`
- `actual_result_summary`
- `scope_risk_addressed`

**Validation rules**:

- Must include a no-behavior-change scope review using `git diff --name-only`.
- Must include report completeness checks for required sections and source
  evidence.
- Must note if Layer 1 or Layer 5 was skipped because no active plugin/test
  surfaces changed.

## Relationships

- A Runtime Surface has zero or more Named-Tool References.
- A Named-Tool Reference belongs to one Allowlist Category.
- A Runtime-by-Capability Matrix Cell cites one or more Capability Mechanics
  Evidence records.
- A Capability Mechanics Evidence record may cite a Sanitized Probe Summary.
- A Directive-Home Recommendation depends on matrix coverage and planned eval
  coverage.
- Downstream Handoffs consume Allowlist Categories, Mechanics Evidence, and the
  Directive-Home Recommendation.
- Verification Evidence proves the report and diff satisfy TACD-001 boundaries.

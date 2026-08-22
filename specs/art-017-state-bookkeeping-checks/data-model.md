# Data Model: Arm The Accidentally-Advisory State Bookkeeping Checks

ART-017 does not add persistent storage. The data model describes existing guard inputs, report keys, and review evidence that the implementation must preserve.

## Entity: State Diagnostic Key

**Fields**:
- `name`: String key emitted in the JSON report.
- `source_check`: Validator function that produces the problem list.
- `problem_values`: List of diagnostic strings.
- `status_evidence_authority`: Boolean determined by explicit membership in `RULE_PROBLEM_KEYS["status-evidence"]`.

**Validation rules**:
- `in_progress_errors`, `duplicate_state_steps`, and `state_order_errors` must be explicit `status-evidence` members.
- No other advisory key may be newly armed by ART-017.
- Existing problem-key names and list-shaped values must remain stable.

## Entity: Rule Intent Record

**Fields**:
- `problem_key`: State Diagnostic Key name.
- `verdict`: One of `gated`, `advisory-deliberate`, or `advisory-accidental`.
- `reason`: Non-empty explanation of why the verdict is correct.

**Validation rules**:
- The three ART-017 keys must move to `gated`.
- Each reason must describe the current-run state invariant protected by the key.
- The set of `gated` intent records must equal the union of explicit rule-map memberships.

## Entity: Status Evidence Rule

**Fields**:
- `rule_name`: `status-evidence`.
- `blocking_keys`: Ordered tuple of problem keys that can move the scoped exit code.

**Validation rules**:
- The rule must include the existing status-evidence keys plus exactly the three ART-017 keys.
- `missing_state_prefixes` and `missing_state_post_items` must remain outside this rule.
- The full JSON report must still include non-member keys.

## Entity: Workflow/State Pair

**Fields**:
- `workflow_path`: Tracked repo-relative workflow path.
- `state_path`: Tracked adjacent `autopilot-state.json`.
- `state.workflow_file`: Repo-relative workflow reference stored in the state file.

**Validation rules**:
- A corpus pair is valid only when both files are tracked, share the same directory, and `state.workflow_file` exactly equals `workflow_path`.
- Workflows without an adjacent tracked state are excluded.
- A state naming another workflow is excluded from the corpus proof rather than silently paired.
- Missing states are never synthesized.

## Entity: Guard Report

**Fields**:
- `status`: Existing top-level run status.
- `workflow_file`: Supplied workflow path.
- `state_file`: Supplied state path.
- `plan_step_count`: Count of loaded state plan steps.
- Problem-key fields: Existing list-valued diagnostic keys.

**Validation rules**:
- ART-017 must preserve top-level shape and existing problem-key names.
- `--rule status-evidence` changes exit-code authority only; it must not hide reported diagnostics.

## Entity: Negative Control Fixture

**Fields**:
- `baseline_workflow`: Known-good workflow Markdown.
- `baseline_state`: Known-good `autopilot-state.json`.
- `mutation`: One isolated state mutation.
- `expected_key`: One of the three ART-017 keys.

**Validation rules**:
- Clean control exits `0` under `--rule status-evidence`.
- Each mutated control exits `1`.
- Each mutated control populates only its target ART-017 problem list among the three new keys.

## Entity: Review Packet

**Fields**:
- `scope_budget`: Projected and actual reviewability footprint.
- `traceability`: Requirement-to-file and requirement-to-verification map.
- `verification`: Targeted tests, generated-artifact refreshes, docs reference checks, and full-suite evidence.
- `generated_artifact_status`: Derived surfaces refreshed or intentionally deferred.
- `integration_note`: ART-008 independence and latest-main rebase/regeneration requirement.

**Validation rules**:
- The packet must order review from authored rule/intent changes, to negative controls, to corpus evidence, to authored prose, to generated artifact refreshes.
- Known gaps must name a follow-up spec or issue.

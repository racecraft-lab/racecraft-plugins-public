# Data Model: TACD-002 Capability Discovery Directive and Agent Updates

## Capability Discovery Directive

**Purpose**: Shared semantic behavior contract for research/context capability selection.

**Fields**:

- `path`: `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`
- `capability_categories`: codebase context, spec context, library documentation, web or domain research, source extraction, installed skills/plugins, repo-local helpers
- `selection_rule`: choose the best installed capability for the task need before fallback, using task fit, source authority/directness, freshness needs, expected evidence quality, and minimal necessary inventory disclosure
- `fallback_rule`: use local files, native platform context, or repo-local helpers when optional installed capabilities are missing, unavailable, or present but unusable
- `reporting_rule`: capability path, evidence, confidence
- `inventory_rule`: do not dump full installed-tool inventories by default

**Validation rules**:

- Must not describe named optional tools as default preferred behavior.
- Must not replace named-tool preference with a fixed vendor-neutral capability order.
- Must preserve formerly named tools as usable only when selected through discovery.
- Must include the exact compact evidence wording from Clarify.
- Fallback confidence must be `medium` or `low`, never `high`.

## Runtime Guidance Surface

**Purpose**: Active Claude or Codex instruction file that controls installed agent behavior.

**Fields**:

- `runtime`: Claude Markdown agent, Codex TOML agent, shared skill reference, or generated payload copy
- `source_path`: repo-relative source file path
- `generated_path`: matching `dist/**` path when applicable
- `directive_binding`: shared pointer, generated rewritten pointer, or compact equivalent
- `metadata_ids`: exact IDs that remain as schema metadata
- `behavior_text`: prose or developer instructions that must be capability-first

**Relationships**:

- Each scoped source guidance surface references or mirrors the Capability Discovery Directive.
- Each generated payload copy traces back to a source guidance surface.

**Validation rules**:

- Scoped Claude surfaces point to the shared directive unless an approved equivalent is recorded.
- Scoped Codex TOML agents may embed a compact equivalent with the exact source-note marker `Capability discovery equivalent: mirrors speckit-pro/skills/speckit-autopilot/references/capability-discovery.md for installed Codex TOML runtime.` when path resolution would break.
- Generated payloads are refreshed from source, not hand-edited as durable source.

## Capability Path Report

**Purpose**: Compact evidence line emitted when research or context discovery informs an answer.

**Fields**:

- `need`: task need, such as codebase context or library documentation
- `selected_capability_or_source`: installed capability, local file, native platform context, or repo-local helper
- `evidence`: citations or local file references
- `confidence`: `high`, `medium`, or `low`
- `reason`: brief confidence rationale

**Validation rules**:

- Must use the Clarify wording format.
- Must name only the selected capability path and material fallback gaps in normal answers.
- Must not include a full installed-tool inventory unless directly requested, needed for troubleshooting, or required as PR evidence.

## Fallback Evidence Disclosure

**Purpose**: Confidence-lowering note used when no installed capability covers the need.

**Fields**:

- `missing_capability`: capability category that was unavailable or unusable
- `fallback_source`: local, native platform, or repo-local fallback used
- `confidence`: `medium` or `low`
- `reason`: why confidence is reduced

**Validation rules**:

- Must preserve normal operation when optional installed capabilities are missing, unavailable, or present but unusable.
- Must not fail solely because a formerly named optional MCP is absent.

## Schema Metadata ID

**Purpose**: Exact identifier that names a tool or dependency because a runtime schema, allowlist, manifest, or generated metadata field requires it.

**Fields**:

- `file`: repo-relative file path
- `field`: metadata field name
- `id_value`: exact preserved ID or pattern
- `classification`: schema metadata, historical/provenance, generated rewrite metadata, or active behavior
- `behavior_scan_result`: whether nearby behavior prose remains capability-first

**Validation rules**:

- Preserved IDs must be classified separately from active behavior guidance.
- Active body text and Codex TOML developer instructions are behavior surfaces, not metadata.
- The PR packet must include a preserved-ID table.

## Generated Payload Copy

**Purpose**: Install-facing runtime artifact generated from source guidance.

**Fields**:

- `payload_root`: `dist/claude/speckit-pro/` or `dist/codex/speckit-pro/`
- `source_root`: `speckit-pro/`
- `builder_command`: `bash scripts/build-plugin-payloads.sh`
- `diff_evidence`: paired source and generated diff review
- `idempotence_evidence`: second rebuild produces no unintended additional changes

**Validation rules**:

- Must be regenerated from source.
- Must not be the durable source of TACD-002 behavior.
- Must be verified with the default deterministic suite.

## PR Review Packet

**Purpose**: Human review contract for the TACD-002 PR.

**Fields**:

- `what_changed`
- `why`
- `non_goals`
- `review_order`
- `scope_budget`
- `traceability`
- `verification_evidence`
- `known_gaps`
- `rollback_or_flags`
- `preserved_id_table`
- `deferred_work`

**Validation rules**:

- Must map major requirements or success criteria to changed files and verification.
- Must include generated payload refresh evidence.
- Must explicitly defer TACD-003 and TACD-004 work.

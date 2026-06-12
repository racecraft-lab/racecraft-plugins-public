# Data Model: Reviewer-ready PR packet contract

## PR Packet

Represents one rendered PR target before creation.

**Fields**

- `schema_version`: Contract version string.
- `packet_id`: Stable packet identifier for validation output.
- `mode`: `single` or `split`.
- `target`: PR target containing `base_branch` and `head_branch`.
- `source_feature_dir`: Repo-relative feature directory that owns the packet.
- `generated_title`: Structured title metadata.
- `body_file`: Repo-relative rendered Markdown body path.
- `required_headings`: Ordered list of required reviewer headings.
- `uat`: How To UAT content plus the required literal `## UAT Runbook` compatibility heading.
- `verification_evidence`: Commands, results, logs, or explicit not-applicable evidence.
- `scope_evidence`: Reviewability budget, changed-file scope, and non-goal evidence.
- `source_markers`: Rendered source/provenance markers outside code fences and comments.
- `editable_fields`: Sanctioned prose fields and exact marker pairs.
- `protected_body_fingerprint`: Normalized fingerprint with editable blocks elided.
- `validation_result_path`: Repo-relative path for packet validation JSON.
- `split_slice`: Optional split identity and source evidence for split mode.

**Validation Rules**

- `target.base_branch` and `target.head_branch` are required for every packet and are the only target values used for `gh pr create --base` and `--head`.
- `body_file` must be a repo-relative rendered Markdown path; absolute paths, parent-directory traversal, directories, and non-Markdown paths are invalid.
- `generated_title.value` must render as `<type>(<scope>): <plain-English description>`.
- Title descriptions must not contain branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, stale placeholders, unexpanded variables, file paths, or banned labels.
- Body must include rendered Markdown `## Summary`, `## What Changed`, `## Why It Matters`, `## How To Review`, `## How To UAT`, `## Verification`, `## Scope`, and `## Known Gaps` headings in that order inside the canonical packet block, plus literal `## UAT Runbook` compatibility content.
- Verification evidence, scope evidence, source markers, and provenance markers are required.
- Scope evidence must include changed-file scope in addition to reviewability budget and non-goals.
- Unknown HTML comments are rejected outside code fences except editable-boundary comments and the legacy `speckit-pro-review-packet-source` compatibility marker.
- Host PR template content may appear only outside the protected canonical packet block.
- `split_slice` is required for split packets and invalid for single packets.

## Generated Title Metadata

Structured title evidence stored inside a PR Packet.

**Fields**

- `value`: Final rendered PR title passed to `gh pr create --title`.
- `type`: Conventional commit type; defaults to `feat`.
- `scope`: Conventional commit scope; implementation packets default to `speckit-pro`.
- `description`: Public-readable action phrase after the colon.
- `source_evidence`: Source used to derive the description.
- `rejected_candidates`: Candidate titles or descriptions rejected during rendering.

**Validation Rules**

- Type and scope overrides require explicit packet metadata.
- Description cannot be inferred from branch names, spec IDs, slice IDs, task IDs, file paths, or free-form body text.
- Single-PR descriptions come from the feature/spec display title normalized into an action phrase.
- Split-PR descriptions come from PR marker `source_boundary.section`, falling back to layer-plan increment names only in legacy layer-plan mode.

## Sanctioned Prose Field

Maintainer-editable narrative region in rendered body text.

**Fields**

- `field_id`: One of `summary`, `what_changed`, or `why_it_matters`.
- `heading`: Parent heading where the field is allowed.
- `start_marker`: Exact full-line start HTML comment.
- `end_marker`: Exact full-line end HTML comment.
- `body_path`: Rendered body file containing the field.

**Validation Rules**

- Marker pairs must be exact full lines.
- Marker field IDs must match the packet JSON.
- `editable_fields` must contain exactly one field each for `summary`, `what_changed`, and `why_it_matters`, in that order.
- Only content inside marker pairs may differ without changing the protected fingerprint.

## Protected Body Fingerprint

Normalized hash for generated body content after sanctioned editable blocks are elided.

**Fields**

- `algorithm`: Hash algorithm name.
- `value`: Hash value.
- `normalization`: Normalization rules used before hashing.
- `elided_fields`: Editable field IDs removed before hashing.

**Validation Rules**

- Any protected body change causes validation failure.
- Editable field changes are allowed only when source markers, UAT content, traceability, scope, verification evidence, known gaps, and governance sections remain intact.

## Packet Validation Result

Deterministic validation output for one packet.

**Fields**

- `schema_version`: Validation record contract version.
- `packet_id`: Packet identifier.
- `mode`: `single` or `split`.
- `target`: PR target evaluated by validation.
- `status`: `passed` or `failed`.
- `title_value`: Rendered title evaluated by validation.
- `body_file`: Rendered body path evaluated by validation.
- `rule_outcomes`: Ordered rule results.
- `failures`: Failed rules and affected fields or sections.
- `remediation_evidence`: Human-readable evidence path, excerpt, or hash detail.
- `pr_blocked`: Boolean indicating whether PR creation must stop.
- `timestamp`: Deterministic or runtime timestamp for the validation event.

**Validation Rules**

- Failed validation sets `pr_blocked` to `true` and exits before PR creation.
- Usage or malformed input errors exit separately from validation failures.
- Split mode writes one result per packet so one failed slice can be identified without hiding other slice outcomes.

## Workflow Event

Concise process log entry appended when validation blocks a packet.

**Fields**

- `event`: Packet validation event name.
- `packet_id`: Packet that failed.
- `validation_result_path`: Path to remediation JSON.
- `summary`: Short operator-readable failure summary.

## Relationships

- A PR Packet owns exactly one Generated Title Metadata object.
- A PR Packet owns one rendered body file and one validation result path.
- A split PR Packet may reference one slice packet as source evidence.
- A Packet Validation Result evaluates exactly one PR Packet.
- Workflow Events reference failed Packet Validation Results.

## State Transitions

```text
draft packet
  -> rendered packet
  -> validation passed
  -> eligible for gh pr create --base --head --title --body-file

draft packet
  -> rendered packet
  -> validation failed
  -> PR creation blocked
  -> validation JSON and workflow event written

rendered packet
  -> sanctioned prose edited
  -> protected fingerprint still matches
  -> validation passed

rendered packet
  -> protected content edited
  -> protected fingerprint mismatch
  -> validation failed
```

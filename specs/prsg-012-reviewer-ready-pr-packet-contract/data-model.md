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
- `generated_title.value` must render as `<type>(<scope>): <plain-English description>`, with spec-backed packets using the active spec id as scope when available.
- Title descriptions must not contain branch refs, slice IDs, PRSG/SPEC/FR/SC/L# tokens, stale placeholders, unexpanded variables, file paths, or banned labels. PRSG/SPEC identifiers are allowed only in the scope before the colon.
- Body must include rendered Markdown `## Summary`, `## What Changed`, `## Why It Matters`, `## How To Review`, `## How To UAT`, `## Verification`, `## Scope`, and `## Known Gaps` headings in that order inside the canonical packet block, plus literal `## UAT Runbook` compatibility content.
- Verification evidence, scope evidence, source markers, and provenance markers are required.
- Scope evidence must include changed-file scope in addition to reviewability budget and non-goals.
- Unknown HTML comments are rejected outside code fences except editable-boundary comments and the legacy `speckit-pro-review-packet-source` compatibility marker.
- Host PR template content may appear only outside the protected canonical packet block.
- `split_slice` is required for split packets and invalid for single packets.
- Missing, unreadable, invalid-JSON, or schema-invalid packet inputs are `input_error` failures, not rendered-content validation failures; they exit `2`, use a synthetic `_input-error-<stable-hash>` identity when `packet_id` is unavailable, and make zero PR creation attempts.

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
- `error_class`: `none`, `validation_failure`, or `input_error`.
- `exit_code`: Validator exit code: `0` for pass, `1` for rendered-content validation failure, or `2` for usage/input error.
- `stderr_line`: Deterministic one-line diagnostic emitted for failed runs.
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
- `resume`: Resume boundary and stale-result policy when validation blocks.
- `prior_successful_prs`: Split-PR references already opened before a later packet blocked.
- `timestamp`: Deterministic or runtime timestamp for the validation event.

**Validation Rules**

- Failed validation sets `pr_blocked` to `true` and exits before PR creation.
- Usage or malformed input errors use `error_class: input_error`, exit `2`, and do not trust packet-owned fields that failed to parse or validate.
- Rendered-content validation failures use `error_class: validation_failure`, exit `1`, and include packet-specific rule outcomes and remediation evidence.
- Passed validation uses `error_class: none`, exit `0`, and sets `pr_blocked` to `false`.
- Split mode writes one result per packet so one failed slice can be identified without hiding other slice outcomes.
- A resume run must revalidate the current rendered packet; stale failed validation records are evidence only and cannot continue blocking after a new passing result supersedes them.

## Packet Resume Evidence

Durable recovery context written when validation blocks a packet.

**Fields**

- `resume_from_packet_id`: Packet or synthetic input-error identity where processing must resume.
- `resume_from_slice_id`: Split slice identity when the blocked packet belongs to a split PR.
- `blocked_until`: Human-readable condition for unblocking, such as fixing a malformed packet or restoring missing evidence.
- `stale_result_policy`: Fixed policy: revalidate current rendered packet before PR creation.
- `prior_successful_prs`: Ordered split PR records that were opened before the block, including slice id, PR number, URL, base branch, head branch, and head SHA when known.

**Validation Rules**

- Resume evidence is required for failed validation results that block PR creation.
- Split-PR resume evidence must preserve earlier successful PR references and must not require closing, relabeling, retargeting, or recreating those PRs.
- The next run must reconcile `prior_successful_prs` with PRSG-009 state surfaces before attempting `gh pr create` for the corrected packet.

## Workflow Event

Concise process log entry appended when validation blocks a packet.

**Fields**

- `event`: Packet validation event name.
- `event_id`: Deterministic id derived from packet or input identity, validation result path, and blocked status.
- `workflow_path`: Active workflow file path under `docs/ai/specs/.process/<workflow-id>-workflow.md`.
- `packet_id`: Packet that failed, or synthetic input-error identity when packet metadata cannot be trusted.
- `mode`: Packet mode when known.
- `target`: PR target when known.
- `validation_result_path`: Repo-relative path to remediation JSON, or `no-path` when no repository file can be safely written.
- `stderr_line`: Deterministic stderr line emitted for the failure.
- `failed_rule_or_reason`: Failed validator rule or input-error reason.
- `remediation_summary`: Short operator-readable action needed to unblock PR creation.
- `pr_blocked`: Boolean indicating PR creation was blocked.
- `resume_from_packet_id`: Packet where the next run resumes, when blocked.
- `prior_successful_prs`: Split PR records already opened before a later packet blocked.
- `summary`: Short operator-readable failure summary.

**Validation Rules**

- Workflow events are appended to the active workflow file, not to arbitrary feature-local files.
- Paths inside the event must be repo-relative.
- `event_id` makes retries idempotent: reruns for the same packet/input, validation result path, and blocked status must supersede or update the same event instead of creating ambiguous duplicates.
- Workflow events are reader-facing evidence only; the packet validation JSON remains authoritative machine-readable evidence.
- Failed rendered-content validation events must include packet identity, mode, target, validation result path, stderr line, failed rule, remediation summary, `pr_blocked: true`, and resume boundary.
- Input-error events may omit mode and target only when the packet input could not be parsed or trusted; they still include the synthetic identity, stderr line, reason, remediation summary, `pr_blocked: true`, and `validation_result_path` or `no-path`.

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
  -> packet fixed
  -> rendered packet revalidated from current content
  -> stale failure superseded
  -> validation passed
  -> eligible for gh pr create --base --head --title --body-file

rendered packet
  -> sanctioned prose edited
  -> protected fingerprint still matches
  -> validation passed

rendered packet
  -> protected content edited
  -> protected fingerprint mismatch
  -> validation failed

split packet N
  -> validation passed
  -> PR opened and recorded in PRSG-009 state
  -> split packet N+1 validation failed
  -> prior PR evidence preserved and resume boundary set to packet N+1
  -> packet N+1 fixed and revalidated
  -> existing PR records reconciled
  -> PR creation resumes at packet N+1 without duplicating packet N
```

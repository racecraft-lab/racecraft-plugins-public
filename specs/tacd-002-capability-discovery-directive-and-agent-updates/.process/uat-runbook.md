# UAT Runbook: tacd-002-capability-discovery-directive-and-agent-updates

| Field | Value |
|-------|-------|
| Spec | tacd-002-capability-discovery-directive-and-agent-updates |
| Branch | tacd-002-capability-discovery-directive-and-agent-updates |
| PR | **PR:** <set on PR open> |
| Generated from | 2026-06-18T04:24:22Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Command | Value |
|---------|-------|
| BUILD | _not available for this project_ |
| TYPECHECK | _not available for this project_ |
| LINT | _not available for this project_ |
| LINT_FIX | _not available for this project_ |
| UNIT_TEST | _not available for this project_ |
| INTEGRATION_TEST | _not available for this project_ |
| SINGLE_FILE_INTEGRATION | _not available for this project_ |

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Agents Choose By Capability Need (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-2"></a>
### User Story 2 - Agents Work Without Optional Capabilities (Priority: P1)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-3"></a>
### User Story 3 - Runtime Guidance Stays Semantically Aligned (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.

<a id="us-4"></a>
### User Story 4 - Generated Payloads Match Source Guidance (Priority: P2)

- [ ] Walk this story end to end and confirm the observable behavior the spec promises.



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Agents Choose By Capability Need (Priority: P1)](#us-1) | see the Per-Story Acceptance Tests block above |
| [User Story 2 - Agents Work Without Optional Capabilities (Priority: P1)](#us-2) | see the Per-Story Acceptance Tests block above |
| [User Story 3 - Runtime Guidance Stays Semantically Aligned (Priority: P2)](#us-3) | see the Per-Story Acceptance Tests block above |
| [User Story 4 - Generated Payloads Match Source Guidance (Priority: P2)](#us-4) | see the Per-Story Acceptance Tests block above |


## Negative-Path Tests


- Runtime or dependency metadata requires exact tool or capability IDs; TACD-002 preserves those IDs unless a generic equivalent is proven.
- Historical archive, changelog, or provenance text mentions older named tools; TACD-002 keeps those references when they are clearly historical rather than active behavior guidance.
- A formerly named optional tool is the best installed capability for a task; agents may still use it through capability discovery without treating it as preferred by default.
- A target runtime cannot follow a shared Markdown pointer from its installed context; installed Codex TOML agents may include a compact approved equivalent with a source-note marker that preserves the same semantic directive.
- Generated `dist/**` payloads are stale after source edits; implementation must refresh them through the repository's generation path.
- A narrow behavior pointer touches setup or limitation wording; the change must stay behavior-only and avoid TACD-003 prerequisite messaging.

## Self-Review Findings

### Findings
- No correctness issues found in the scoped source or generated payload diffs.
- Preserved named IDs are confined to allowlist/dependency metadata or generated runtime metadata.
- The reviewability task gate size block remains recorded; final reviewability backstop still decides PR side effects.
### Verification Reviewed
- `git diff --check`: passed.
- `bash tests/speckit-pro/run-all.sh --layer 1`: `1024/1024` passed.
- `bash tests/speckit-pro/run-all.sh`: `3041/3041` passed.
---

## Sign-off

Advisory only — these checkboxes block nothing.

- [ ] Reviewer walked every Per-Story Acceptance Test above.
- [ ] Reviewer confirmed the Negative-Path Tests behave as described.
- [ ] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

# UAT Runbook: prsg-009-multi-pr-emission

| Field | Value |
|-------|-------|
| Spec | prsg-009-multi-pr-emission |
| Branch | prsg-009-multi-pr-emission |
| PR | https://github.com/racecraft-lab/racecraft-plugins-public/pull/145 |
| Generated from | 2026-06-11T00:30:40Z |



## Env Setup

Run these from the repository root before walking the acceptance tests.

| Gate | Command |
|------|---------|
| STRUCTURAL | `bash tests/speckit-pro/run-all.sh --layer 1` |
| SCRIPT_UNIT | `bash tests/speckit-pro/run-all.sh --layer 4` |
| PARITY_DRY_RUN | `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run` |
| DEFAULT_VERIFY | `bash tests/speckit-pro/run-all.sh` |

Notes:

- This is a shell-only plugin repository. There is no separate build, lint, typecheck, or package step.
- The multi-PR UAT below uses dry-run candidates and fixtures. It must not open real GitHub PRs.
- The dry-run full-regression evidence path mirrors `specs/prsg-009-multi-pr-emission/.process/emission/` under `UAT_TMP` so the contract is exercised without modifying the repo.
- If you want focused feedback while reviewing, run the named Layer 4 test files first, then run `DEFAULT_VERIFY`.

## Per-Story Acceptance Tests

<a id="us-1"></a>
### User Story 1 - Emit ordered slice PRs from the layer plan (Priority: P1)

- [x] Run the focused emitter tests:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Generate local dry-run candidate files. This does not create branches, push, or open PRs.

  ```bash
  UAT_TMP="$(mktemp -d)"
  mkdir -p "$UAT_TMP/specs/prsg-009-multi-pr-emission/.process/emission" "$UAT_TMP/candidates"
  printf '%s\n' 'DEFAULT_VERIFY passed for PRSG-009 UAT' \
    > "$UAT_TMP/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
  printf '%s\n' \
    'tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh' \
    'speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh' \
    'speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh' \
    > "$UAT_TMP/changed-files.txt"

  bash speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh \
    --layer-plan tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/layer-plans/valid-three-slice.json \
    --state tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/emission-state/empty-autopilot-state.json \
    --feature-branch prsg-009-multi-pr-emission \
    --base main \
    --base-sha 0123456789abcdef \
    --full-verification-evidence "$UAT_TMP/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt" \
    --changed-files "$UAT_TMP/changed-files.txt" \
    --candidate-dir "$UAT_TMP/candidates"
  ```

- [x] Inspect the candidate state for review order and Style B branch topology.

  ```bash
  jq -r '.multi_pr_emission.slices[] | [.review_order, .slice_id, .expected_branch, .expected_base_branch] | @tsv' \
    "$UAT_TMP/candidates/multi-pr-emission-state.candidate.json"
  ```

  Expected rows:

  ```text
  1	foundation	prsg-009-multi-pr-emission/01-foundation	main
  2	us1	prsg-009-multi-pr-emission/02-us1	prsg-009-multi-pr-emission/01-foundation
  3	us2	prsg-009-multi-pr-emission/03-us2	prsg-009-multi-pr-emission/02-us1
  ```

- [x] Inspect the candidate command capture and confirm every PR command uses explicit base, head, and body file flags.

  ```bash
  jq -r '.operations[] | select(.action == "gh_pr_create") | "\(.slice_id): base=\(.command[4]) head=\(.command[6]) body_flag=\(.command[7])"' \
    "$UAT_TMP/candidates/commands.candidate.json"
  ```

  Expected rows:

  ```text
  foundation: base=main head=prsg-009-multi-pr-emission/01-foundation body_flag=--body-file
  us1: base=prsg-009-multi-pr-emission/01-foundation head=prsg-009-multi-pr-emission/02-us1 body_flag=--body-file
  us2: base=prsg-009-multi-pr-emission/02-us1 head=prsg-009-multi-pr-emission/03-us2 body_flag=--body-file
  ```

- [x] Confirm the candidate slice packets exist and carry reviewer evidence instead of fake PR rows.

  ```bash
  find "$UAT_TMP/candidates/slice-packets" -maxdepth 1 -type f -print | sort
  jq '.schemaVersion, .records' "$UAT_TMP/candidates/prs.candidate.json"
  jq '.full_verification_evidence, .scoped_verification.commands[0].evidence_path' \
    "$UAT_TMP/candidates/slice-packets/foundation.json"
  ```

<a id="us-2"></a>
### User Story 2 - Persist PR table and resume evidence after each slice (Priority: P2)

- [x] Run the fixture-backed emitter persistence and resume tests:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Inspect the test coverage for the persistence and resume paths.

  ```bash
  rg -n "US2 persistence|successful emission persists|resume reconciles|closed unmerged|gh pr create failure|post-PR PRS persistence failure" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

  Confirm the tests cover:

  - state, PRS manifest, SPEC-MOC, and workflow updates after successful slice PRs
  - resume by expected head/base without duplicating an existing PR
  - closed unmerged PRs blocking without replacement PR creation
  - `gh pr create` failure recording recoverable state without a PRS row
  - post-PR persistence failure preserving the opened PR metadata and keeping `next_slice_id` on the blocked slice

- [x] Run the PRS renderer tests for schema v1/v2 compatibility and MOC table output.

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh
  ```

- [x] Inspect the PRS renderer assertions for schema v2 reviewer rows.

  ```bash
  rg -n "schemaVersion 2|open row displays head_sha|merged row prefers merged_sha|malformed prs.json" \
    tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh
  ```

  Confirm schema v2 rows render order, slice, PR, status, branch, base, SHA, scope, and verification evidence; open rows use `head_sha`, merged rows prefer `merged_sha`, and malformed manifests fail safe.

- [x] Run the PR body generator tests for slice-packet rendering and UAT runbook embedding.

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh
  ```

- [x] Inspect the generated slice packet fixture used by PR body tests.

  ```bash
  jq '.slice_id, .review_order, .base_branch, .head_branch, .declared_files, .scoped_verification.commands, .full_verification_evidence' \
    tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/slice-packets/valid-foundation.json
  ```

<a id="us-3"></a>
### User Story 3 - Define stack topology, scoped CI, and restack behavior (Priority: P3)

- [x] Run the focused restack tests:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-restack.sh
  ```

- [x] Run the restack helper manually in dry-run mode. This must not mutate git or GitHub state.

  ```bash
  bash speckit-pro/skills/speckit-autopilot/scripts/restack.sh \
    --state tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-stack-state.json \
    --manifest tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-prs-manifest.json \
    --base main \
    --remote origin \
    --start-after prsg-009-multi-pr-emission/01-foundation
  ```

- [x] Inspect the dry-run JSON and confirm remaining branches are retargeted in order while preserving scope.

  ```bash
  bash speckit-pro/skills/speckit-autopilot/scripts/restack.sh \
    --state tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-stack-state.json \
    --manifest tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/restack/remaining-prs-manifest.json \
    --base main \
    --remote origin \
    --start-after prsg-009-multi-pr-emission/01-foundation \
    | jq '.dry_run, .status, .scope_preserved, [.operations[] | {slice_id, old_base, new_base, applied, result}]'
  ```

  Expected behavior:

  - `dry_run` is `true`
  - `status` is `success`
  - `scope_preserved` is `true`
  - the first remaining slice retargets to `main`
  - each later remaining slice retargets to the immediately preceding remaining slice branch

- [x] Run the emitter tests again for scoped CI evidence, no-op scoped tests, and later-slice failure isolation.

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "US3 scoped verification evidence|no_scoped_tests|later scoped verification failure" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

  Confirm scoped verification is recorded in slice packets and state, no-scoped-test slices still get required evidence, and a later scoped failure stops before `gh pr create` without rewinding earlier opened PR rows.

- [x] Confirm Claude and Codex references carry the same multi-PR behavior.

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-post-implementation-reference.sh
  bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run
  ```



## FR Coverage Matrix

| Story | Acceptance test |
|-------|-----------------|
| [User Story 1 - Emit ordered slice PRs from the layer plan (Priority: P1)](#us-1) | `test-multi-pr-emission.sh` plus local `--candidate-dir` inspection |
| [User Story 2 - Persist PR table and resume evidence after each slice (Priority: P2)](#us-2) | `test-multi-pr-emission.sh`, `test-generate-spec-index.sh`, and `test-generate-pr-body.sh` |
| [User Story 3 - Define stack topology, scoped CI, and restack behavior (Priority: P3)](#us-3) | `test-restack.sh`, `test-multi-pr-emission.sh`, `test-post-implementation-reference.sh`, and Layer 8 parity dry-run |


## Negative-Path Tests

Run the focused command, then inspect the named assertions with `rg` if you need to review the exact fixture and expected failure mode.

- [x] Invalid, input-error, malformed, or missing layer-plan evidence blocks before mutation:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "invalid layer-plan|input-error layer-plan|malformed layer-plan|missing full regression evidence" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Duplicate durable state keys block resume:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "duplicate state slice_id|duplicate state rejection" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Undeclared changed files block before command capture:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "undeclared changed files" tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Single-slice plans still use the multi-PR emission contract and do not flatten into the old all-changes PR path:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "single-slice" tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Invalid slice packets fail without overwriting an existing PR body:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh
  rg -n "Invalid --slice-packet|Malformed --slice-packet|Missing --slice-packet|leaves existing output unchanged" \
    tests/speckit-pro/layer4-scripts/test-generate-pr-body.sh
  ```

- [x] Closed unmerged PRs and PR creation failures block without duplicate PR creation:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "closed unmerged PR|gh pr create failure" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] GitHub PR creation succeeds but state, PRS, MOC, or workflow persistence fails afterward:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "post-PR PRS persistence failure|persistence failed after PR opened" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] `.process/prs.json` absent, empty, stale, schema v1, schema v2, or malformed behavior is explicit:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh
  rg -n "PRS empty/absent|schemaVersion 1|schemaVersion 2|malformed prs.json|stale result" \
    tests/speckit-pro/layer4-scripts/test-generate-spec-index.sh
  ```

- [x] Scoped verification passes for an earlier slice but fails for a later slice:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  rg -n "later scoped verification failure|failed scoped verification" \
    tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
  ```

- [x] Lower-stack squash merge restack is dry-run-first and maps dirty worktree, GitHub failure, and conflicts to distinct recovery evidence:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-restack.sh
  rg -n "dry-run default|dirty worktree|gh failure|retarget conflict" \
    tests/speckit-pro/layer4-scripts/test-restack.sh
  ```

- [x] Claude and Codex mirrored references differ or parity fixture structure is broken:

  ```bash
  bash tests/speckit-pro/layer4-scripts/test-post-implementation-reference.sh
  bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run
  ```

## Self-Review Findings

1. **Tests executed?** PASS. This repo has no separate build, typecheck, lint, or package command. The relevant shell checks are `bash tests/speckit-pro/run-all.sh --layer 1`, `bash tests/speckit-pro/run-all.sh --layer 4`, `bash tests/speckit-pro/layer8-parity/run-parity-fixtures.sh --dry-run`, and `bash tests/speckit-pro/run-all.sh`.
2. **Edge cases?** PASS. The focused negative paths are covered in Layer 4: invalid/input-error/malformed layer plans, duplicate state keys, invalid branch names, undeclared changed files, single-slice no-flattening, closed PR resume, PR-create failure, post-PR persistence failure, no-scoped-test evidence, later scoped verification failure, invalid slice packets, PRS schema v1/v2/error rendering, and restack dry-run/apply/failure mapping.
3. **Requirements matched?** PASS. The UAT checks trace the three user stories to the shipped shell surfaces: `multi-pr-emission.sh`, `generate-pr-body.sh`, `generate-spec-index.sh`, `restack.sh`, the post-implementation reference contract, and the Layer 8 parity fixture structure.
4. **Follow-up?** PASS. This runbook is intentionally local and fixture-backed. It does not require opening live GitHub PRs. Live Layer 8 parity remains an opt-in AI eval path; this runbook uses the dry-run parity structure check.

## UAT Execution Notes

- 2026-06-11: Full UAT was executed from the PR worktree. Structural validation passed `915/915`, script-unit validation passed `1187/1187` after remediation, Layer 8 parity dry-run passed `6/6`, and default verification passed `2292/2292`.
- Remediated issue: the first script-unit run found a privacy-scan failure caused by local GitHub account names in workflow prose. The prose now uses generic credential wording, and `test-privacy-scan` passes `9/9`.
- Remediated issue: the US1 dry-run command initially wrote full-regression evidence outside the required `specs/prsg-009-multi-pr-emission/.process/emission/` layout. The runbook now mirrors that path under `UAT_TMP`, and the dry-run emitter passes without mutating git or GitHub state.
---

## Sign-off

Advisory only - these checkboxes block nothing.

- [x] Reviewer walked every Per-Story Acceptance Test above.
- [x] Reviewer confirmed the Negative-Path Tests behave as described.
- [x] Reviewer is satisfied the PR delivers the behavior the spec promised.

## Rollback

git revert <SHA>; see plan.md for data-migration considerations

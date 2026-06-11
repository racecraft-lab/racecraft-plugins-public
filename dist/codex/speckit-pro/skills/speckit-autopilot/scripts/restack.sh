#!/usr/bin/env bash
# restack.sh - PRSG-009 dry-run-first restack helper.

set -euo pipefail

usage() {
  printf 'Usage: restack.sh --state <json> --manifest <json> --base <branch> --remote <remote> --start-after <branch> [--apply]\n' >&2
}

STATE_FILE=""
MANIFEST_FILE=""
BASE_BRANCH=""
REMOTE_NAME=""
START_AFTER=""
DRY_RUN=true
GH_STACK_BIN="${RESTACK_GH_STACK_BIN:-gh-stack}"
GH_STACK_JSON='{"available":false,"inspected":false,"mutating":false}'

require_jq() {
  command -v jq >/dev/null 2>&1 || {
    printf 'restack.sh: input_error: jq is required\n' >&2
    exit 2
  }
}

emit_output() {
  local status="$1" exit_code="$2" operations_json="${3:-[]}" recovery_json="${4:-null}"
  jq -cn \
    --argjson dry_run "$DRY_RUN" \
    --arg status "$status" \
    --argjson exit_code "$exit_code" \
    --arg base "${BASE_BRANCH:-unknown}" \
    --arg remote "${REMOTE_NAME:-unknown}" \
    --arg start_after "${START_AFTER:-}" \
    --argjson operations "$operations_json" \
    --argjson gh_stack "$GH_STACK_JSON" \
    --argjson recovery "$recovery_json" \
    '{
      dry_run: $dry_run,
      status: $status,
      exit_code: $exit_code,
      base: $base,
      remote: $remote,
      start_after: (if $start_after == "" then null else $start_after end),
      scope_preserved: true,
      gh_stack: $gh_stack,
      recovery_evidence: $recovery,
      operations: $operations
    }'
}

fail_with_status() {
  local status="$1" exit_code="$2" message="$3" operations_json="${4:-[]}" recovery_json="${5:-null}"
  emit_output "$status" "$exit_code" "$operations_json" "$recovery_json"
  printf 'restack.sh: %s: %s\n' "$status" "$message" >&2
  exit "$exit_code"
}

input_error() {
  local message="$1"
  fail_with_status "input_error" 2 "$message"
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --state)
      [ "$#" -ge 2 ] || input_error "missing value for --state"
      STATE_FILE="$2"
      shift 2
      ;;
    --manifest)
      [ "$#" -ge 2 ] || input_error "missing value for --manifest"
      MANIFEST_FILE="$2"
      shift 2
      ;;
    --base)
      [ "$#" -ge 2 ] || input_error "missing value for --base"
      BASE_BRANCH="$2"
      shift 2
      ;;
    --remote)
      [ "$#" -ge 2 ] || input_error "missing value for --remote"
      REMOTE_NAME="$2"
      shift 2
      ;;
    --start-after)
      [ "$#" -ge 2 ] || input_error "missing value for --start-after"
      START_AFTER="$2"
      shift 2
      ;;
    --apply)
      DRY_RUN=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      input_error "unknown argument $1"
      ;;
  esac
done

require_jq

[ -n "$STATE_FILE" ] || input_error "missing required option --state"
[ -n "$MANIFEST_FILE" ] || input_error "missing required option --manifest"
[ -n "$BASE_BRANCH" ] || input_error "missing required option --base"
[ -n "$REMOTE_NAME" ] || input_error "missing required option --remote"
[ -n "$START_AFTER" ] || input_error "missing required option --start-after"

[ -r "$STATE_FILE" ] || input_error "state not readable: $STATE_FILE"
[ -r "$MANIFEST_FILE" ] || input_error "manifest not readable: $MANIFEST_FILE"

jq -e . "$STATE_FILE" >/dev/null 2>&1 || input_error "invalid state JSON"
jq -e . "$MANIFEST_FILE" >/dev/null 2>&1 || input_error "invalid manifest JSON"

if ! jq -e '
  (.multi_pr_emission.slices | type == "array")
  and all(.multi_pr_emission.slices[];
    (.slice_id | type == "string")
    and (.review_order | type == "number" and . == floor and . >= 1)
    and (.expected_branch | type == "string")
    and (.expected_base_branch | type == "string")
    and (.status | type == "string")
  )
' "$STATE_FILE" >/dev/null 2>&1; then
  input_error "invalid restack state shape"
fi

if ! jq -e '
  .schemaVersion == 2
  and (.records | type == "array")
  and all(.records[];
    (.slice_id | type == "string")
    and (.branch | type == "string")
    and (.base_branch | type == "string")
    and (.status | type == "string")
  )
' "$MANIFEST_FILE" >/dev/null 2>&1; then
  input_error "invalid PRS manifest shape"
fi

inspect_gh_stack() {
  if [ -n "$GH_STACK_BIN" ] && command -v "$GH_STACK_BIN" >/dev/null 2>&1; then
    "$GH_STACK_BIN" status --json >/dev/null 2>&1 || true
    GH_STACK_JSON='{"available":true,"inspected":true,"mutating":false}'
  else
    GH_STACK_JSON='{"available":false,"inspected":false,"mutating":false}'
  fi
}

start_order="$(
  jq -r --arg start "$START_AFTER" '
    (.multi_pr_emission.slices // [])
    | map(select(.expected_branch == $start or .slice_id == $start))
    | .[0].review_order // empty
  ' "$STATE_FILE"
)"
[ -n "$start_order" ] || input_error "start-after slice not found: $START_AFTER"

operations_json="$(
  jq -n \
    --slurpfile state "$STATE_FILE" \
    --slurpfile manifest "$MANIFEST_FILE" \
    --arg base "$BASE_BRANCH" \
    --argjson start_order "$start_order" '
      ($state[0].multi_pr_emission.slices // []) as $slices
      | ($manifest[0].records // []) as $records
      | (
          $slices
          | map(select(.review_order > $start_order and .status != "merged" and .status != "closed"))
          | sort_by(.review_order)
        ) as $remaining
      | $remaining
      | to_entries
      | map(
          .key as $idx
          | .value as $slice
          | (($records | map(select(.slice_id == $slice.slice_id)) | .[0]) // {}) as $record
          | {
              slice_id: $slice.slice_id,
              branch: $slice.expected_branch,
              old_base: ($record.base_branch // $slice.expected_base_branch),
              new_base: (if $idx == 0 then $base else $remaining[$idx - 1].expected_branch end),
              action: "retarget",
              applied: false,
              result: "planned_scope_preserved",
              pr_number: ($record.pr_number // null),
              declared_files: ($slice.declared_files // [])
            }
        )
    '
)"

inspect_gh_stack

if [ "$DRY_RUN" = true ]; then
  emit_output "success" 0 "$operations_json"
  exit 0
fi

dirty_output="$(git status --porcelain 2>/dev/null || true)"
if [ -n "$dirty_output" ]; then
  recovery_json="$(jq -cn '{retry_policy:"clean worktree and rerun restack.sh --apply", failed_operation:null, evidence_path:null}')"
  fail_with_status "dirty_worktree" 3 "worktree has uncommitted changes" "$operations_json" "$recovery_json"
fi

operation_count="$(printf '%s' "$operations_json" | jq 'length')"
idx=0
while [ "$idx" -lt "$operation_count" ]; do
  operation_json="$(printf '%s' "$operations_json" | jq -c --argjson idx "$idx" '.[$idx]')"
  branch="$(printf '%s' "$operation_json" | jq -r '.branch')"
  pr_number="$(printf '%s' "$operation_json" | jq -r '.pr_number // empty')"
  new_base="$(printf '%s' "$operation_json" | jq -r '.new_base')"

  if [ -z "$pr_number" ]; then
    recovery_json="$(jq -cn --argjson op "$operation_json" '{retry_policy:"restore PR manifest row and rerun restack.sh --apply", failed_operation:$op, evidence_path:null}')"
    fail_with_status "git_gh_failure" 4 "missing PR number for $branch" "$operations_json" "$recovery_json"
  fi

  gh_stderr="$(mktemp "${TMPDIR:-/tmp}/restack-gh.XXXXXX")"
  if ! gh pr edit "$pr_number" --base "$new_base" 2>"$gh_stderr"; then
    gh_error="$(cat "$gh_stderr" 2>/dev/null || true)"
    rm -f "$gh_stderr"
    if [[ "$gh_error" == *conflict* || "$gh_error" == *Conflict* ]]; then
      recovery_json="$(jq -cn --argjson op "$operation_json" '{retry_policy:"resolve conflict and rerun restack.sh --apply", failed_operation:$op, evidence_path:null}')"
      fail_with_status "conflicts" 1 "restack conflict while retargeting $branch" "$operations_json" "$recovery_json"
    fi
    recovery_json="$(jq -cn --argjson op "$operation_json" '{retry_policy:"inspect git/gh failure and rerun restack.sh --apply", failed_operation:$op, evidence_path:null}')"
    fail_with_status "git_gh_failure" 4 "gh pr edit failed for $branch" "$operations_json" "$recovery_json"
  fi
  rm -f "$gh_stderr"
  idx=$((idx + 1))
done

operations_json="$(
  printf '%s' "$operations_json" | jq '
    map(.applied = true | .result = "applied_scope_preserved")
  '
)"

emit_output "success" 0 "$operations_json" "$(jq -cn '{retry_policy:"run DEFAULT_VERIFY before treating merge evidence as current", failed_operation:null, evidence_path:null}')"

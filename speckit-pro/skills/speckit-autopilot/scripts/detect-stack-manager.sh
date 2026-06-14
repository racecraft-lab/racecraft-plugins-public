#!/usr/bin/env bash
# detect-stack-manager.sh - PRSG-014 optional gh-stack decision helper.

set -euo pipefail

usage() {
  printf 'Usage: detect-stack-manager.sh --phase <emission|restack> --operation <detect|link|sync|restack> --feature-dir <specs/name> [--prs <prs-v2.json>] [--marker-plan <pr-marker-plan.json>] [--base <branch>] [--evidence-path <path>]\n' >&2
}

PHASE=""
OPERATION="detect"
FEATURE_DIR=""
PRS_FILE=""
MARKER_PLAN=""
BASE_BRANCH="main"
EVIDENCE_PATH=""
PERSIST=true

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$REPO_ROOT" ] || REPO_ROOT="$(pwd -P)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

require_jq() {
  command -v jq >/dev/null 2>&1 || {
    printf 'detect-stack-manager.sh: input_error: jq is required\n' >&2
    exit 2
  }
}

emit_input_error() {
  local message="$1"
  jq -cn --arg message "$message" \
    '{script:"detect-stack-manager",status:"input_error",exit_code:2,message:$message}'
  printf 'detect-stack-manager.sh: input_error: %s\n' "$message" >&2
  exit 2
}

write_json_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir" || emit_input_error "cannot create evidence directory: $dir"
  if [ -e "$target" ] && [ ! -f "$target" ]; then
    emit_input_error "evidence path is not a file: $target"
  fi
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")" || emit_input_error "cannot create temp evidence file"
  printf '%s\n' "$content" > "$tmp"
  jq -e . "$tmp" >/dev/null 2>&1 || {
    rm -f "$tmp"
    emit_input_error "candidate evidence JSON failed validation"
  }
  mv -f "$tmp" "$target"
}

tail_limit() {
  local path="$1"
  if [ ! -f "$path" ]; then
    printf ''
    return
  fi
  tail -n 120 "$path" | LC_ALL=C awk '
    BEGIN { limit = 16384; used = 0 }
    {
      line = $0
      bytes = length(line) + 1
      if (used + bytes > limit) exit
      print line
      used += bytes
    }
  '
}

repo_relative_path() {
  local path="$1" resolved
  case "$path" in
    "$REPO_ROOT"/*)
      printf '%s\n' "${path#"$REPO_ROOT"/}"
      ;;
    "$REPO_ROOT")
      printf '.\n'
      ;;
    ./*)
      printf '%s\n' "${path#./}"
      ;;
    *)
      resolved="$path"
      printf '%s\n' "$resolved"
      ;;
  esac
}

is_safe_repo_path() {
  local path="$1"
  case "$path" in
    ""|/*|*..*|*[$'\n\r\t']*|*[\;\|\&\`\"\']*)
      return 1
      ;;
    *)
      return 0
      ;;
  esac
}

is_safe_ref() {
  local value="$1"
  case "$value" in
    ""|-*|*[$'\n\r\t ']*|*..*|*//*) return 1 ;;
  esac
  [[ "$value" =~ ^[A-Za-z0-9._/-]+$ ]]
}

semver_supported() {
  local version="$1" major minor patch
  if [[ ! "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    return 1
  fi
  major="${BASH_REMATCH[1]}"
  minor="${BASH_REMATCH[2]}"
  patch="${BASH_REMATCH[3]}"
  if [ "$major" -gt 0 ]; then
    return 0
  fi
  if [ "$minor" -gt 0 ]; then
    return 0
  fi
  [ "$patch" -ge 5 ]
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --phase)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --phase"
      PHASE="$2"
      shift 2
      ;;
    --operation)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --operation"
      OPERATION="$2"
      shift 2
      ;;
    --feature-dir)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --feature-dir"
      FEATURE_DIR="$2"
      shift 2
      ;;
    --prs)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --prs"
      PRS_FILE="$2"
      shift 2
      ;;
    --marker-plan)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --marker-plan"
      MARKER_PLAN="$2"
      shift 2
      ;;
    --base)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --base"
      BASE_BRANCH="$2"
      shift 2
      ;;
    --evidence-path)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --evidence-path"
      EVIDENCE_PATH="$2"
      shift 2
      ;;
    --no-persist)
      PERSIST=false
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      emit_input_error "unknown argument $1"
      ;;
  esac
done

require_jq

case "$PHASE" in
  emission|restack) ;;
  "") emit_input_error "missing required option --phase" ;;
  *) emit_input_error "invalid phase: $PHASE" ;;
esac
case "$OPERATION" in
  detect|link|sync|restack) ;;
  *) emit_input_error "invalid operation: $OPERATION" ;;
esac
[ -n "$FEATURE_DIR" ] || emit_input_error "missing required option --feature-dir"
is_safe_repo_path "$FEATURE_DIR" || emit_input_error "unsafe feature dir: $FEATURE_DIR"
case "$FEATURE_DIR" in
  specs/*) ;;
  *) emit_input_error "feature dir must be under specs/" ;;
esac
is_safe_ref "$BASE_BRANCH" || emit_input_error "unsafe base branch: $BASE_BRANCH"

if [ -n "$PRS_FILE" ]; then
  is_safe_repo_path "$PRS_FILE" || emit_input_error "unsafe PRS path: $PRS_FILE"
  [ -r "$PRS_FILE" ] || emit_input_error "PRS file not readable: $PRS_FILE"
  jq -e '.schemaVersion == 2 and (.records | type == "array")' "$PRS_FILE" >/dev/null 2>&1 || emit_input_error "invalid PRS v2 manifest"
fi
if [ -n "$MARKER_PLAN" ]; then
  is_safe_repo_path "$MARKER_PLAN" || emit_input_error "unsafe marker plan path: $MARKER_PLAN"
  [ -r "$MARKER_PLAN" ] || emit_input_error "marker plan not readable: $MARKER_PLAN"
  jq -e '.schema_version == "pr-marker-plan.v1" and (.markers | type == "array")' "$MARKER_PLAN" >/dev/null 2>&1 || emit_input_error "invalid marker plan"
fi

if [ -z "$EVIDENCE_PATH" ] && [ "$PERSIST" = true ]; then
  EVIDENCE_PATH="$FEATURE_DIR/.process/stack-manager/$PHASE/$OPERATION/preflight/decision.json"
fi
if [ -n "$EVIDENCE_PATH" ]; then
  is_safe_repo_path "$EVIDENCE_PATH" || emit_input_error "unsafe evidence path: $EVIDENCE_PATH"
  case "$EVIDENCE_PATH" in
    "$FEATURE_DIR"/.process/*|docs/ai/specs/.process/*) ;;
    *) emit_input_error "evidence path must be under feature .process or docs/ai/specs/.process" ;;
  esac
fi

topology_json="$(
  if [ -n "$PRS_FILE" ]; then
    jq -c '
      {
        source: "prs-v2",
        records: ((.records // []) | sort_by(.review_order) | map({
          review_order,
          slice_id,
          branch,
          base_branch,
          pr_number: (.pr_number // null),
          pr_url: (.pr_url // null),
          head_sha: (.head_sha // null),
          status
        })),
        expected_order: ((.records // []) | sort_by(.review_order) | map(.branch))
      }
    ' "$PRS_FILE"
  elif [ -n "$MARKER_PLAN" ]; then
    jq -c '
      {
        source: "pr-marker-plan",
        records: ((.markers // []) | sort_by(.review_order) | map({
          review_order,
          slice_id: .id,
          branch: .id,
          base_branch: "",
          pr_number: null,
          pr_url: null,
          head_sha: null,
          status: (.implementation_checkpoint.status // "pending")
        })),
        expected_order: ((.markers // []) | sort_by(.review_order) | map(.id))
      }
    ' "$MARKER_PLAN"
  else
    jq -cn '{source:"none",records:[],expected_order:[]}'
  fi
)"

unsafe_branch="$(
  printf '%s' "$topology_json" | jq -r '
    (.records // [])
    | map(.branch, .base_branch)
    | map(select(. != null and . != ""))
    | .[]
  ' | while IFS= read -r ref; do
    if ! is_safe_ref "$ref"; then
      printf '%s\n' "$ref"
      break
    fi
  done
)"
[ -z "$unsafe_branch" ] || emit_input_error "unsafe topology ref: $unsafe_branch"

gh_available=false
gh_version=""
version_supported=false
support_status="missing"
gh_reason="gh stack is not available"
read_exit=null
read_parsed=false
matched_expected=false
view_stdout_tail=""
view_stderr_tail=""
observed_order_json="[]"

if command -v gh >/dev/null 2>&1; then
  gh_available=true
  version_stdout="$(mktemp "${TMPDIR:-/tmp}/detect-stack-version.stdout.XXXXXX")"
  version_stderr="$(mktemp "${TMPDIR:-/tmp}/detect-stack-version.stderr.XXXXXX")"
  version_rc=0
  gh stack --version >"$version_stdout" 2>"$version_stderr" || version_rc=$?
  version_output="$(cat "$version_stdout" "$version_stderr" 2>/dev/null || true)"
  gh_version="$(printf '%s\n' "$version_output" | LC_ALL=C grep -Eo '[0-9]+[.][0-9]+[.][0-9]+' | head -1 || true)"
  rm -f "$version_stdout" "$version_stderr"
  if [ "$version_rc" -ne 0 ] && printf '%s\n' "$version_output" | LC_ALL=C grep -qiE 'unknown command: stack|unknown command .*stack|not a gh command'; then
    support_status="missing"
    gh_reason="gh stack is not available"
  elif [ "$version_rc" -ne 0 ] || [ -z "$gh_version" ]; then
    support_status="ambiguous"
    gh_reason="gh stack version could not be determined"
  elif semver_supported "$gh_version"; then
    version_supported=true
    view_stdout="$(mktemp "${TMPDIR:-/tmp}/detect-stack-view.stdout.XXXXXX")"
    view_stderr="$(mktemp "${TMPDIR:-/tmp}/detect-stack-view.stderr.XXXXXX")"
    view_rc=0
    gh stack view --json >"$view_stdout" 2>"$view_stderr" || view_rc=$?
    read_exit="$view_rc"
    view_stdout_tail="$(tail_limit "$view_stdout")"
    view_stderr_tail="$(tail_limit "$view_stderr")"
    if [ "$view_rc" -eq 0 ] && jq -e . "$view_stdout" >/dev/null 2>&1; then
      read_parsed=true
      observed_order_json="$(
        jq -c '
          def branch_name:
            .branch // .name // .headRefName // .head // .ref // empty;
          if type == "array" then
            [ .[] | branch_name ]
          elif type == "object" and (.branches | type == "array") then
            [ .branches[] | branch_name ]
          elif type == "object" and (.stack | type == "array") then
            [ .stack[] | branch_name ]
          elif type == "object" and (.items | type == "array") then
            [ .items[] | branch_name ]
          else
            []
          end
        ' "$view_stdout"
      )"
      expected_order_json="$(printf '%s' "$topology_json" | jq -c '.expected_order')"
      expected_count="$(printf '%s' "$expected_order_json" | jq 'length')"
      observed_count="$(printf '%s' "$observed_order_json" | jq 'length')"
      if [ "$expected_count" -eq 0 ]; then
        matched_expected=true
      elif [ "$observed_count" -gt 0 ] && [ "$expected_order_json" = "$observed_order_json" ]; then
        matched_expected=true
      fi
      if [ "$matched_expected" = true ]; then
        support_status="supported"
        gh_reason="gh stack version, read-only proof, and topology checks passed"
      else
        support_status="topology_incompatible"
        gh_reason="gh stack view topology does not match expected PRS/marker order"
      fi
    else
      support_status="read_only_proof_failed"
      gh_reason="gh stack view --json failed or returned invalid JSON"
    fi
    rm -f "$view_stdout" "$view_stderr"
  else
    support_status="unsupported_version"
    gh_reason="gh stack version is below the supported PRSG-014 matrix"
  fi
fi

selected_manager="explicit-gh"
reason="$gh_reason; using explicit gh fallback before mutation"
fallback_reason_json="$(jq -cn --arg reason "$gh_reason" '$reason')"
fallback_allowed=true
mutation_status="none"
first_mutating_command_id_json=null
supported=false
repo_enabled=false

if [ "$support_status" = "supported" ]; then
  selected_manager="gh-stack"
  reason="gh stack supported for $PHASE $OPERATION"
  fallback_reason_json=null
  mutation_status="planned"
  first_mutating_command_id_json="$(jq -cn --arg id "stack-${OPERATION}" '$id')"
  supported=true
  repo_enabled=true
fi

evidence_path_json=null
if [ -n "$EVIDENCE_PATH" ]; then
  evidence_path_json="$(jq -cn --arg path "$EVIDENCE_PATH" '$path')"
fi

command_plan_json="$(
  jq -cn \
    --arg manager "$selected_manager" \
    --arg operation "$OPERATION" \
    --arg phase "$PHASE" \
    --arg base "$BASE_BRANCH" \
    --arg feature_dir "$FEATURE_DIR" \
    --argjson topology "$topology_json" '
      def explicit_head: (($topology.records // [])[0].branch // "HEAD");
      def explicit_slice: (($topology.records // [])[0].slice_id // null);
      def explicit_review_order: (($topology.records // [])[0].review_order // null);
      def explicit_body: "\($feature_dir)/.process/pr-packets/\(explicit_slice // "stack").md";
      def explicit_title: "chore(PRSG-014): stacked PR";
      def stack_operands:
        ($topology.records // [])
        | map(if (.pr_number // null) != null then (.pr_number | tostring) else .branch end);
      if $manager == "gh-stack" and $operation == "restack" then
        [{
          id: "stack-restack",
          action: "rebase_upstack",
          manager: "gh-stack",
          argv: ["gh", "stack", "rebase", "--upstack", ((stack_operands | .[0]) // "HEAD")],
          mutates: true,
          mutation_boundary: true,
          slice_id: explicit_slice,
          review_order: explicit_review_order,
          preconditions: ["gh_stack_supported", "read_only_proof_matched", "topology_validated"],
          reason: "Supported gh stack rebase --upstack path"
        }]
      elif $manager == "gh-stack" then
        [{
          id: "stack-link",
          action: "link_stack",
          manager: "gh-stack",
          argv: (["gh", "stack", "link", "--base", $base] + stack_operands),
          mutates: true,
          mutation_boundary: true,
          slice_id: explicit_slice,
          review_order: explicit_review_order,
          preconditions: ["gh_stack_supported", "read_only_proof_matched", "packets_validated", "topology_validated"],
          reason: "Supported gh stack link path after packet-owned PR reconciliation"
        }]
      else
        if $operation == "restack" then
          [{
            id: "explicit-gh-restack-fallback",
            action: "retarget_base",
            manager: "explicit-gh",
            argv: ["gh", "pr", "edit", (((($topology.records // [])[0].pr_number // 0) | tostring)), "--base", $base],
            mutates: true,
            mutation_boundary: true,
            slice_id: explicit_slice,
            review_order: explicit_review_order,
            preconditions: ["gh_stack_not_supported_before_mutation", "topology_validated"],
            reason: "Explicit gh restack fallback before any gh stack mutation"
          }]
        else
          [{
            id: "explicit-gh-fallback",
            action: "create_pr",
            manager: "explicit-gh",
            argv: ["gh", "pr", "create", "--base", $base, "--head", explicit_head, "--body-file", explicit_body, "--title", explicit_title],
            mutates: true,
            mutation_boundary: true,
            slice_id: explicit_slice,
            review_order: explicit_review_order,
            preconditions: ["gh_stack_not_supported_before_mutation", "packets_validated", "topology_validated"],
            reason: "Explicit gh fallback before any gh stack mutation"
          }]
        end
      end
    '
)"

decision_json="$(
  jq -cn \
    --arg phase "$PHASE" \
    --arg operation "$OPERATION" \
    --arg selected_manager "$selected_manager" \
    --arg reason "$reason" \
    --argjson fallback_reason "$fallback_reason_json" \
    --argjson fallback_allowed "$fallback_allowed" \
    --arg mutation_status "$mutation_status" \
    --argjson first_mutating_command_id "$first_mutating_command_id_json" \
    --argjson gh_available "$gh_available" \
    --argjson supported "$supported" \
    --arg gh_reason "$gh_reason" \
    --arg version "$gh_version" \
    --argjson version_supported "$version_supported" \
    --argjson repo_enabled "$repo_enabled" \
    --arg support_status "$support_status" \
    --argjson read_exit "$read_exit" \
    --argjson read_parsed "$read_parsed" \
    --argjson matched_expected "$matched_expected" \
    --arg view_stdout_tail "$view_stdout_tail" \
    --arg view_stderr_tail "$view_stderr_tail" \
    --argjson topology "$topology_json" \
    --argjson observed_order "$observed_order_json" \
    --argjson command_plan "$command_plan_json" \
    --argjson evidence_path "$evidence_path_json" '
      {
        schema_version: "stack-manager-decision.v1",
        phase: $phase,
        operation: $operation,
        selected_manager: $selected_manager,
        reason: $reason,
        fallback_reason: $fallback_reason,
        fallback_allowed: $fallback_allowed,
        mutation_boundary: {
          status: $mutation_status,
          first_mutating_command_id: $first_mutating_command_id,
          fallback_after_boundary_allowed: false
        },
        gh_stack: {
          available: $gh_available,
          supported: $supported,
          reason: $gh_reason,
          extension_owner: "github",
          extension_name: "gh-stack",
          version: (if $version == "" then null else $version end),
          version_supported: $version_supported,
          repo_enabled: $repo_enabled,
          support_status: $support_status,
          invocation: [["gh", "stack", "--version"], ["gh", "stack", "view", "--json"]]
        },
        read_only_proof: {
          argv: ["gh", "stack", "view", "--json"],
          exit_status: $read_exit,
          parsed: $read_parsed,
          matched_expected_topology: $matched_expected,
          stdout_tail: $view_stdout_tail,
          stderr_tail: $view_stderr_tail,
          evidence_path: $evidence_path
        },
        topology_compatibility: {
          compatible: $matched_expected,
          source: $topology.source,
          mismatch_reason: (if $matched_expected then null else "observed stack order did not match expected topology" end),
          expected_order: ($topology.expected_order // []),
          observed_order: $observed_order
        },
        command_plan: $command_plan,
        topology: {
          pre_mutation: ($topology.records // []),
          post_mutation: []
        },
        recovery: null,
        evidence_path: $evidence_path
      }
    '
)"

if [ "$PERSIST" = true ]; then
  [ -n "$EVIDENCE_PATH" ] || emit_input_error "missing evidence path for persisted decision"
  write_json_atomic "$EVIDENCE_PATH" "$decision_json"
fi
printf '%s\n' "$decision_json"

#!/usr/bin/env bash
# final-reviewability-backstop.sh - PRSG-010A stop-before-PR final gate.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || cd "$SCRIPT_DIR/../../../.." && pwd -P)"

if [ -d "$REPO_ROOT/speckit-pro/skills/speckit-autopilot/contracts" ]; then
  CONTRACT_ROOT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/contracts"
else
  CONTRACT_ROOT="$SKILL_ROOT/contracts"
fi

STATE_SCHEMA="$CONTRACT_ROOT/final-reviewability-gate-state.schema.json"
PACKET_SCHEMA="$CONTRACT_ROOT/reslicing-packet.schema.json"

usage() {
  printf 'Usage: final-reviewability-backstop.sh --feature-dir <specs/name> --feature-branch <branch> [--gate-result <json> --gate-exit-code <0|1|2> | --diff-range <range>] [--state-output <json>] [--packet-output <json>] [--layer-plan <json>] [--sizing-result <json>] [--changed-files <txt>] [--full-verification-evidence <path>]\n' >&2
}

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  value="${value//$'\r'/\\r}"
  value="${value//$'\t'/\\t}"
  printf '%s' "$value"
}

emit_input_error() {
  local message="$1" escaped
  escaped="$(json_escape "$message")"
  printf '{"script":"final-reviewability-backstop","status":"input_error","exit_code":2,"message":"%s"}\n' "$escaped"
  printf 'final-reviewability-backstop.sh: input_error: %s\n' "$message" >&2
  exit 2
}

require_jq() {
  command -v jq >/dev/null 2>&1 || {
    printf 'final-reviewability-backstop.sh: input_error: jq is required\n' >&2
    exit 2
  }
}

write_json_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir" || emit_input_error "cannot create output directory: $dir"
  if [ -e "$target" ] && [ ! -f "$target" ]; then
    emit_input_error "output path is not a file: $target"
  fi
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")" || emit_input_error "cannot create temp file for $target"
  printf '%s\n' "$content" > "$tmp" || {
    rm -f "$tmp"
    emit_input_error "cannot write temp file for $target"
  }
  jq -e . "$tmp" >/dev/null 2>&1 || {
    rm -f "$tmp"
    emit_input_error "invalid JSON assembled for $target"
  }
  mv -f "$tmp" "$target" || {
    rm -f "$tmp"
    emit_input_error "cannot move temp file into $target"
  }
}

repo_relative_path() {
  local raw="$1" path
  if [ -z "$raw" ]; then
    printf ''
    return
  fi
  case "$raw" in
    "$REPO_ROOT"/*)
      printf '%s\n' "${raw#"$REPO_ROOT"/}"
      return
      ;;
  esac
  case "$raw" in
    */specs/*) printf 'specs/%s\n' "${raw#*/specs/}" ;;
    */docs/*) printf 'docs/%s\n' "${raw#*/docs/}" ;;
    */.specify/*) printf '.specify/%s\n' "${raw#*/.specify/}" ;;
    */speckit-pro/*) printf 'speckit-pro/%s\n' "${raw#*/speckit-pro/}" ;;
    *) printf '%s\n' "$raw" ;;
  esac
}

json_string_or_null() {
  local value="$1"
  if [ -n "$value" ]; then
    printf '%s' "$value" | jq -R .
  else
    printf 'null'
  fi
}

json_file_or_empty_object() {
  local path="$1"
  if [ -n "$path" ] && [ -r "$path" ] && jq -e 'type == "object"' "$path" >/dev/null 2>&1; then
    jq -c . "$path"
  else
    printf '{}'
  fi
}

changed_file_count() {
  local path="$1"
  if [ -n "$path" ] && [ -r "$path" ]; then
    sed '/^[[:space:]]*$/d' "$path" | wc -l | tr -d ' '
  else
    printf '0'
  fi
}

validate_contract_files() {
  [ -r "$STATE_SCHEMA" ] || emit_input_error "state schema not readable: $STATE_SCHEMA"
  [ -r "$PACKET_SCHEMA" ] || emit_input_error "packet schema not readable: $PACKET_SCHEMA"
  jq empty "$STATE_SCHEMA" "$PACKET_SCHEMA" >/dev/null 2>&1 || emit_input_error "contract schema JSON is invalid"
}

normalize_exceptions() {
  local gate_file="$1"
  jq -c '
    def path_provenance:
      (.path // "") as $p
      | if ($p | test("(^|/)\\.process/")) then "process"
        elif ($p | test("(^|/)(templates?|PULL_REQUEST_TEMPLATE)(/|$)|template"; "i")) then "template"
        elif ($p | test("(^|/)(generated|dist|build)(/|$)")) then "generated"
        elif ($p | test("pr[-_]?description|pr[-_]?body|pull_request_template"; "i")) then "pr-description"
        else "contract"
        end;
    def normalized($honored):
      {
        path: ((.path // "unknown") | tostring),
        line: ((.line // 1) | tonumber),
        class: (if ((.class // null) == "refactor" or (.class // null) == "infra" or (.class // null) == "upgrade") then .class else null end),
        provenance: (.provenance // path_provenance),
        branch_added: (.branch_added // false),
        honored: $honored,
        reason: ((.reason // "") | tostring)
      };
    def valid:
      (.class == "refactor" or .class == "infra" or .class == "upgrade")
      and .provenance == "contract"
      and .branch_added == true
      and (.path | length > 0)
      and (.line >= 1);
    def reject_reason:
      if .provenance != "contract" then "rejected exception provenance: " + .provenance
      elif .branch_added != true then "rejected exception because it is not branch-added"
      elif (.class == null) then "rejected exception class"
      else "rejected exception evidence"
      end;
    [(.exceptions.accepted // [])[]] as $accepted_raw
    | [(.exceptions.rejected // [])[]] as $rejected_raw
    | (if (($accepted_raw | length) == 0) and (.exception_honored == true) and (.exception_class != null) then
         [{
           path: "unknown",
           line: 1,
           class: .exception_class,
           provenance: "unknown",
           branch_added: false,
           reason: "missing line-anchored exception evidence"
         }]
       else $accepted_raw end) as $accepted_candidates
    | ($accepted_candidates | map(normalized(true))) as $accepted_normalized
    | {
        accepted: ($accepted_normalized | map(select(valid) | .reason = (if (.reason | length) > 0 then .reason else "accepted operator-owned typed exception" end))),
        rejected: (
          ($accepted_normalized | map(select(valid | not) | .honored = false | .reason = reject_reason))
          + ($rejected_raw | map(normalized(false) | .honored = false | .reason = (if (.reason | length) > 0 then .reason else reject_reason end)))
        )
      }
  ' "$gate_file"
}

build_metrics() {
  local gate_file="$1"
  jq -c '{
    reviewable_loc: (.reviewable_loc // 0),
    production_files: (.production_files // 0),
    total_files: (.total_files // 0),
    primary_surface_count: (.primary_surface_count // 0),
    primary_surfaces: (.primary_surfaces // []),
    greenfield: (.greenfield // false),
    thresholds: (.thresholds // {}),
    warnings: (.warnings // []),
    blockers: (.blockers // [])
  }' "$gate_file"
}

gate_reason() {
  local gate_file="$1" status="$2"
  jq -r --arg status "$status" '
    if (.error // "") != "" then .error
    elif $status == "block" and ((.blockers // []) | length) > 0 then (.blockers | join("; "))
    elif ($status == "warn" or $status == "pass" or $status == "exception") and ((.warnings // []) | length) > 0 then (.warnings | join("; "))
    else "final reviewability gate " + $status
    end
  ' "$gate_file"
}

state_shape_is_valid() {
  local json="$1"
  printf '%s' "$json" | jq -e '
    type == "object"
    and .schemaVersion == 1
    and .kind == "final_reviewability_gate"
    and (.status | IN("pass", "warn", "exception", "block", "error"))
    and (.metrics | type == "object")
    and (.exception | type == "object")
    and (.blocked_operations | type == "array")
    and .pr_created == false
    and .pr == null
  ' >/dev/null
}

packet_shape_is_valid() {
  local json="$1"
  printf '%s' "$json" | jq -e '
    type == "object"
    and .schemaVersion == 1
    and .kind == "final_reviewability_reslicing_packet"
    and .gate.status == "block"
    and (.operator_steps | type == "array" and length >= 3)
    and (.blocked_operations | index("pr-body-generation") != null)
    and (.blocked_operations | index("single-pr-create") != null)
    and (.blocked_operations | index("multi-pr-emission") != null)
    and .no_pr_assertions.pr_created == false
    and .no_pr_assertions.gh_pr_create_invoked == false
    and .no_pr_assertions.multi_pr_emission_invoked == false
  ' >/dev/null
}

GATE_RESULT=""
GATE_EXIT_CODE=""
DIFF_RANGE="origin/main...HEAD"
FEATURE_DIR=""
FEATURE_BRANCH=""
SPEC_ID=""
TITLE=""
BASE_REF="main"
HEAD_REF="HEAD"
BASE_SHA=""
STATE_OUTPUT=""
PACKET_OUTPUT=""
LAYER_PLAN=""
SIZING_RESULT=""
CHANGED_FILES=""
FULL_VERIFICATION_EVIDENCE=""
TIMESTAMP=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --gate-result) [ "$#" -ge 2 ] || emit_input_error "missing value for --gate-result"; GATE_RESULT="$2"; shift 2 ;;
    --gate-exit-code) [ "$#" -ge 2 ] || emit_input_error "missing value for --gate-exit-code"; GATE_EXIT_CODE="$2"; shift 2 ;;
    --diff-range) [ "$#" -ge 2 ] || emit_input_error "missing value for --diff-range"; DIFF_RANGE="$2"; shift 2 ;;
    --feature-dir) [ "$#" -ge 2 ] || emit_input_error "missing value for --feature-dir"; FEATURE_DIR="$2"; shift 2 ;;
    --feature-branch) [ "$#" -ge 2 ] || emit_input_error "missing value for --feature-branch"; FEATURE_BRANCH="$2"; shift 2 ;;
    --spec-id) [ "$#" -ge 2 ] || emit_input_error "missing value for --spec-id"; SPEC_ID="$2"; shift 2 ;;
    --title) [ "$#" -ge 2 ] || emit_input_error "missing value for --title"; TITLE="$2"; shift 2 ;;
    --base-ref) [ "$#" -ge 2 ] || emit_input_error "missing value for --base-ref"; BASE_REF="$2"; shift 2 ;;
    --head-ref) [ "$#" -ge 2 ] || emit_input_error "missing value for --head-ref"; HEAD_REF="$2"; shift 2 ;;
    --base-sha) [ "$#" -ge 2 ] || emit_input_error "missing value for --base-sha"; BASE_SHA="$2"; shift 2 ;;
    --state-output) [ "$#" -ge 2 ] || emit_input_error "missing value for --state-output"; STATE_OUTPUT="$2"; shift 2 ;;
    --packet-output) [ "$#" -ge 2 ] || emit_input_error "missing value for --packet-output"; PACKET_OUTPUT="$2"; shift 2 ;;
    --layer-plan) [ "$#" -ge 2 ] || emit_input_error "missing value for --layer-plan"; LAYER_PLAN="$2"; shift 2 ;;
    --sizing-result) [ "$#" -ge 2 ] || emit_input_error "missing value for --sizing-result"; SIZING_RESULT="$2"; shift 2 ;;
    --changed-files) [ "$#" -ge 2 ] || emit_input_error "missing value for --changed-files"; CHANGED_FILES="$2"; shift 2 ;;
    --full-verification-evidence) [ "$#" -ge 2 ] || emit_input_error "missing value for --full-verification-evidence"; FULL_VERIFICATION_EVIDENCE="$2"; shift 2 ;;
    --timestamp) [ "$#" -ge 2 ] || emit_input_error "missing value for --timestamp"; TIMESTAMP="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) usage; emit_input_error "unknown argument $1" ;;
  esac
done

require_jq
validate_contract_files

[ -n "$FEATURE_DIR" ] || emit_input_error "missing required option --feature-dir"
[ -n "$FEATURE_BRANCH" ] || emit_input_error "missing required option --feature-branch"
[ -n "$STATE_OUTPUT" ] || STATE_OUTPUT="$FEATURE_DIR/.process/final-reviewability/gate-state.json"
[ -n "$PACKET_OUTPUT" ] || PACKET_OUTPUT="$FEATURE_DIR/.process/final-reviewability/reslicing-packet.json"
[ -n "$SPEC_ID" ] || SPEC_ID="$FEATURE_BRANCH"
[ -n "$TITLE" ] || TITLE="$FEATURE_BRANCH"
[ -n "$TIMESTAMP" ] || TIMESTAMP="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

GATE_TMP=""
GATE_TMP_OWNED=false
cleanup() {
  if [ "$GATE_TMP_OWNED" = "true" ] && [ -n "$GATE_TMP" ]; then
    rm -f "$GATE_TMP"
  fi
}
trap cleanup EXIT

if [ -n "$GATE_RESULT" ]; then
  [ -r "$GATE_RESULT" ] || emit_input_error "gate result not readable: $GATE_RESULT"
  GATE_TMP="$GATE_RESULT"
  GATE_TMP_OWNED=false
  [ -n "$GATE_EXIT_CODE" ] || GATE_EXIT_CODE=0
else
  GATE_TMP="$(mktemp "${TMPDIR:-/tmp}/final-reviewability-gate.XXXXXX")"
  GATE_TMP_OWNED=true
  set +e
  "$SCRIPT_DIR/reviewability-gate.sh" diff "$DIFF_RANGE" > "$GATE_TMP"
  GATE_EXIT_CODE=$?
  set -e
fi

jq -e 'type == "object"' "$GATE_TMP" >/dev/null 2>&1 || emit_input_error "gate result JSON is invalid"

raw_status="$(jq -r '.status // empty' "$GATE_TMP")"
if [ "$GATE_EXIT_CODE" = "2" ] || [ -z "$raw_status" ] || [ "$raw_status" = "error" ]; then
  final_status="error"
else
  final_status="$raw_status"
fi

exception_json="$(normalize_exceptions "$GATE_TMP")"
valid_exception_count="$(printf '%s' "$exception_json" | jq -r '.accepted | length')"

case "$final_status" in
  pass|warn)
    exit_code=0
    ;;
  exception)
    if [ "$valid_exception_count" -gt 0 ]; then
      exit_code=0
    else
      final_status="block"
      exit_code=1
    fi
    ;;
  block)
    exit_code=1
    ;;
  error)
    exit_code=2
    ;;
  *)
    final_status="error"
    exit_code=2
    ;;
esac

metrics_json="$(build_metrics "$GATE_TMP")"
reason="$(gate_reason "$GATE_TMP" "$final_status")"
state_packet_path="$(repo_relative_path "$PACKET_OUTPUT")"
state_packet_path_json="$(json_string_or_null "$state_packet_path")"
if [ "$final_status" != "block" ]; then
  state_packet_path_json=null
fi

blocked_ops_json='[]'
if [ "$final_status" = "block" ]; then
  blocked_ops_json='["pr-body-generation","single-pr-create","multi-pr-emission"]'
fi

exception_state_json="$(
  printf '%s' "$exception_json" | jq -c --arg status "$final_status" '
    if $status == "exception" then
      {honored: true, class: .accepted[0].class, evidence: .accepted}
    else
      {honored: false, class: null, evidence: .rejected}
    end
  '
)"

state_json="$(
  jq -cn \
    --arg status "$final_status" \
    --arg gate_result "${raw_status:-error}" \
    --arg gate_reason "$reason" \
    --argjson metrics "$metrics_json" \
    --argjson exception "$exception_state_json" \
    --argjson blocked_operations "$blocked_ops_json" \
    --arg timestamp "$TIMESTAMP" \
    --argjson reslicing_packet_path "$state_packet_path_json" \
    '{
      schemaVersion: 1,
      kind: "final_reviewability_gate",
      status: $status,
      gate_result: $gate_result,
      gate_reason: $gate_reason,
      metrics: $metrics,
      exception: $exception,
      blocked_operations: $blocked_operations,
      timestamp: $timestamp,
      pr_created: false,
      pr: null,
      reslicing_packet_path: $reslicing_packet_path
    }'
)"

state_shape_is_valid "$state_json" || emit_input_error "assembled final gate state failed shape validation"
write_json_atomic "$STATE_OUTPUT" "$state_json"

if [ "$final_status" != "block" ]; then
  printf '%s\n' "$state_json"
  exit "$exit_code"
fi

sizing_json="$(json_file_or_empty_object "$SIZING_RESULT")"
layer_plan_json="$(json_file_or_empty_object "$LAYER_PLAN")"
changed_count="$(changed_file_count "$CHANGED_FILES")"
state_rel="$(repo_relative_path "$STATE_OUTPUT")"
layer_plan_rel="$(repo_relative_path "$LAYER_PLAN")"
sizing_rel="$(repo_relative_path "$SIZING_RESULT")"
changed_rel="$(repo_relative_path "$CHANGED_FILES")"
full_verification_rel="$(repo_relative_path "$FULL_VERIFICATION_EVIDENCE")"

layer_available=false
layer_status="missing"
slice_count=0
if [ -n "$LAYER_PLAN" ] && [ -r "$LAYER_PLAN" ]; then
  if printf '%s' "$layer_plan_json" | jq -e '.tool == "plan-layers" and .status == "ok" and (.increments | type == "array")' >/dev/null 2>&1; then
    layer_available=true
    layer_status="available"
    slice_count="$(printf '%s' "$layer_plan_json" | jq -r '.increments | length')"
  else
    layer_status="invalid"
  fi
fi

sizing_route="$(printf '%s' "$sizing_json" | jq -r '.route // "split-PR"')"
sizing_summary="$(printf '%s' "$sizing_json" | jq -r '.summary // .reason // "Final diff gate requires re-slicing through PRSG-007 sizing context."')"
sizing_thresholds="$(printf '%s' "$sizing_json" | jq -c '.thresholds // {}')"

resume_from="prsg-009-multi-pr-emission"
if [ -z "$SIZING_RESULT" ] || [ ! -r "$SIZING_RESULT" ]; then
  resume_from="prsg-007-routing"
elif [ "$layer_status" != "available" ]; then
  resume_from="prsg-008-layer-planning"
fi

packet_json="$(
  jq -cn \
    --arg branch "$FEATURE_BRANCH" \
    --arg feature_dir "$FEATURE_DIR" \
    --arg spec_id "$SPEC_ID" \
    --arg title "$TITLE" \
    --arg base_ref "$BASE_REF" \
    --arg head_ref "$HEAD_REF" \
    --arg base_sha "$BASE_SHA" \
    --argjson changed_files "$changed_count" \
    --arg changed_files_path "$changed_rel" \
    --arg gate_reason "$reason" \
    --argjson metrics "$metrics_json" \
    --argjson exceptions "$exception_json" \
    --argjson blocked_operations "$blocked_ops_json" \
    --arg sizing_source "$sizing_rel" \
    --arg sizing_summary "$sizing_summary" \
    --arg sizing_route "$sizing_route" \
    --argjson sizing_thresholds "$sizing_thresholds" \
    --argjson layer_available "$layer_available" \
    --arg layer_status "$layer_status" \
    --arg layer_plan_path "$layer_plan_rel" \
    --argjson slice_count "$slice_count" \
    --arg state_path "$state_rel" \
    --arg full_verification_evidence_path "$full_verification_rel" \
    --arg resume_from "$resume_from" \
    --argjson layer_plan "$layer_plan_json" \
    '{
      schemaVersion: 1,
      kind: "final_reviewability_reslicing_packet",
      feature: {
        branch: $branch,
        feature_dir: $feature_dir,
        spec_id: $spec_id,
        title: $title
      },
      diff: {
        base_ref: $base_ref,
        head_ref: $head_ref,
        base_sha: $base_sha,
        changed_files: $changed_files,
        changed_files_path: $changed_files_path,
        gate_input_summary: "final diff reviewability gate"
      },
      gate: {
        status: "block",
        reason: $gate_reason,
        metrics: $metrics
      },
      exceptions: {
        accepted: [],
        rejected: (($exceptions.rejected + $exceptions.accepted) | map(.honored = false))
      },
      blocked_operations: $blocked_operations,
      no_pr_assertions: {
        pr_created: false,
        pr: null,
        pr_body_generated: false,
        single_pr_create_invoked: false,
        gh_pr_create_invoked: false,
        multi_pr_emission_invoked: false
      },
      sizing: {
        source: (if $sizing_source == "" then "missing" else $sizing_source end),
        summary: $sizing_summary,
        route: $sizing_route,
        thresholds: $sizing_thresholds
      },
      layer_plan: {
        available: $layer_available,
        status: $layer_status,
        path: (if $layer_plan_path == "" then null else $layer_plan_path end),
        slice_count: $slice_count
      },
      handoff: {
        tool: "multi-pr-emission.sh",
        command_template: ("speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh --layer-plan " + (if $layer_plan_path == "" then "<layer-plan.json>" else $layer_plan_path end) + " --state " + $state_path + " --feature-branch " + $branch + " --base " + $base_ref + " --base-sha " + $base_sha + " --full-verification-evidence " + (if $full_verification_evidence_path == "" then "<full-verification-evidence>" else $full_verification_evidence_path end) + " --changed-files " + (if $changed_files_path == "" then "<changed-files.txt>" else $changed_files_path end)),
        required_inputs: [
          (if $layer_plan_path == "" then "<layer-plan.json>" else $layer_plan_path end),
          $state_path,
          (if $full_verification_evidence_path == "" then "<full-verification-evidence>" else $full_verification_evidence_path end),
          (if $changed_files_path == "" then "<changed-files.txt>" else $changed_files_path end)
        ],
        layer_plan_path: (if $layer_plan_path == "" then "<layer-plan.json>" else $layer_plan_path end),
        state_path: $state_path,
        full_verification_evidence_path: (if $full_verification_evidence_path == "" then "<full-verification-evidence>" else $full_verification_evidence_path end),
        changed_files_path: (if $changed_files_path == "" then "<changed-files.txt>" else $changed_files_path end)
      },
      suggested_slice_boundaries: (
        if ($layer_plan.increments // [] | length) > 0 then
          $layer_plan.increments | map({
            id: .id,
            title: (.title // .id),
            rationale: "Regenerate or emit this PRSG-008 slice as an independently reviewable PR.",
            paths: (.files // [])
          })
        else
          [{
            id: "reslice-1",
            title: "Regenerate reviewable slices",
            rationale: "No usable layer plan was available at the final gate boundary.",
            paths: [$feature_dir]
          }]
        end
      ),
      operator_steps: [
        {
          order: 1,
          phase: "prsg-007-routing",
          action: "Re-run atomicity routing and sizing context.",
          command: ("speckit-pro/skills/speckit-autopilot/scripts/atomicity-route.sh " + $feature_dir),
          required_paths: [$feature_dir],
          when: "Use when sizing or route evidence is missing, stale, or conflicts with the final diff.",
          expected_result: "A current PRSG-007 route and thresholds are available for re-slicing."
        },
        {
          order: 2,
          phase: "prsg-008-layer-planning",
          action: "Regenerate the layer plan from the current tasks.",
          command: ("speckit-pro/skills/speckit-autopilot/scripts/plan-layers.sh " + $feature_dir),
          required_paths: [$feature_dir, ($feature_dir + "/tasks.md")],
          when: "Use when the layer plan is missing, invalid, or stale after PRSG-007 routing.",
          expected_result: "A valid PRSG-008 layer plan with reviewable slice boundaries is available."
        },
        {
          order: 3,
          phase: "prsg-009-multi-pr-emission",
          action: "Hand off valid slices to multi-PR emission.",
          command: ("speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh --layer-plan " + (if $layer_plan_path == "" then "<layer-plan.json>" else $layer_plan_path end) + " --state " + $state_path + " --feature-branch " + $branch + " --base " + $base_ref + " --base-sha " + $base_sha),
          required_paths: [
            (if $layer_plan_path == "" then "<layer-plan.json>" else $layer_plan_path end),
            $state_path
          ],
          when: "Use only after PRSG-007 routing and PRSG-008 layer planning are current and valid.",
          expected_result: "PRSG-009 emits reviewable PR candidates instead of one oversized PR."
        }
      ],
      resume: {
        status: "reslicing_required",
        next_action: (
          if $resume_from == "prsg-007-routing" then "Refresh PRSG-007 routing and sizing evidence."
          elif $resume_from == "prsg-008-layer-planning" then "Regenerate PRSG-008 layer plan."
          else "Hand valid slices to PRSG-009 multi-PR emission."
          end
        ),
        operator_message: "Final reviewability gate blocked before PR body generation, gh pr create, or multi-PR emission.",
        resume_from: $resume_from,
        blocked_until: "A valid reviewable slice plan exists or an explicit operator-owned typed exception is committed."
      }
    }'
)"

packet_shape_is_valid "$packet_json" || emit_input_error "assembled re-slicing packet failed shape validation"
write_json_atomic "$PACKET_OUTPUT" "$packet_json"

printf '%s\n' "$state_json"
exit "$exit_code"

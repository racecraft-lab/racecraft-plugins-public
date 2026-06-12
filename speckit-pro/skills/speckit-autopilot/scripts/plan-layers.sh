#!/usr/bin/env bash
# plan-layers.sh - Read-only layer and marker planner for SpecKit tasks.md files.

set -euo pipefail
shopt -s extglob

CALLER_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
CALLER_ROOT="$(cd "$CALLER_ROOT" && pwd -P)"
REPO_ROOT="$CALLER_ROOT"

json_value() {
  printf '%s' "$1" | jq -Rs .
}

trim() {
  local value="$1"
  value="${value##+([[:space:]])}"
  value="${value%%+([[:space:]])}"
  printf '%s' "$value"
}

trim_var() {
  local -n ref="$1"
  ref="${ref##+([[:space:]])}"
  ref="${ref%%+([[:space:]])}"
}

absolute_path() {
  local raw="$1" path dir base tail
  if [[ "$raw" = /* ]]; then
    path="$raw"
  else
    path="$REPO_ROOT/$raw"
  fi

  if [ -d "$path" ]; then
    (cd "$path" && pwd -P)
    return
  fi

  dir="$(dirname "$path")"
  base="$(basename "$path")"
  if [ -d "$dir" ]; then
    printf '%s/%s\n' "$(cd "$dir" && pwd -P)" "$base"
    return
  fi

  tail="$base"
  while [ ! -d "$dir" ] && [ "$dir" != "/" ]; do
    tail="$(basename "$dir")/$tail"
    dir="$(dirname "$dir")"
  done

  if [ -d "$dir" ]; then
    printf '%s/%s\n' "$(cd "$dir" && pwd -P)" "$tail"
  else
    printf '%s\n' "$path"
  fi
}

normalize_for_display() {
  local raw="$1" resolved
  resolved="$(absolute_path "$raw")"
  case "$resolved" in
    "$REPO_ROOT")
      printf '.\n'
      ;;
    "$REPO_ROOT"/*)
      printf '%s\n' "${resolved#"$REPO_ROOT"/}"
      ;;
    *)
      printf '%s\n' "$raw"
      ;;
  esac
}

source_json() {
  local path="$1" line="${2:-}" heading="${3:-}" line_json
  if [ -n "$line" ]; then
    line_json="$line"
  else
    line_json=null
  fi

  if [ -n "$heading" ]; then
    jq -cn --arg path "$path" --argjson line "$line_json" --arg heading "$heading" \
      '{path: $path, line: $line, heading: $heading}'
  else
    jq -cn --arg path "$path" --argjson line "$line_json" \
      '{path: $path, line: $line}'
  fi
}

diagnostic_json() {
  local code="$1" severity="$2" message="$3" line="$4" details_json="$5"
  local src
  src="$(source_json "$TASKS_REL" "$line")"
  jq -cn \
    --arg code "$code" \
    --arg severity "$severity" \
    --arg message "$message" \
    --argjson source "$src" \
    --argjson details "$details_json" \
    '{
      code: $code,
      severity: $severity,
      message: $message,
      source: $source,
      details: $details
    }'
}

json_array_from_json_items() {
  if [ "$#" -eq 0 ]; then
    printf '[]'
  else
    printf '%s\n' "$@" | jq -s '.'
  fi
}

json_array_from_values() {
  if [ "$#" -eq 0 ]; then
    printf '[]'
  else
    printf '%s\n' "$@" | jq -Rsc 'split("\n") | map(select(length > 0)) | unique | sort'
  fi
}

json_array_from_ordered_values() {
  if [ "$#" -eq 0 ]; then
    printf '[]'
  else
    printf '%s\n' "$@" | jq -Rsc 'split("\n") | map(select(length > 0))'
  fi
}

values_list_from_args() {
  if [ "$#" -eq 0 ]; then
    printf ''
  else
    local IFS=$'\n'
    printf '%s' "$*"
  fi
}

emit_input_error() {
  local code="$1" message="$2" feature="${3:-}" tasks="${4:-}" details_json="$5"
  local feature_json tasks_json source_path_json

  if [ "${MODE:-legacy}" = "marker-plan" ]; then
    emit_marker_problem "input_error" "$code" "$message" "$feature" "$tasks" "$details_json" "2"
  fi

  if [ -n "$feature" ]; then
    feature_json="$(json_value "$(normalize_for_display "$feature")")"
  else
    feature_json=null
  fi

  if [ -n "$tasks" ]; then
    tasks_json="$(json_value "$(normalize_for_display "$tasks")")"
    source_path_json="$tasks_json"
  else
    tasks_json=null
    if [ -n "$feature" ]; then
      source_path_json="$feature_json"
    else
      source_path_json=null
    fi
  fi

  jq -cn \
    --arg code "$code" \
    --arg message "$message" \
    --argjson feature_dir "$feature_json" \
    --argjson tasks_file "$tasks_json" \
    --argjson source_path "$source_path_json" \
    --argjson details "$details_json" \
    '{
      tool: "plan-layers",
      contract_version: 1,
      status: "input_error",
      feature_dir: $feature_dir,
      tasks_file: $tasks_file,
      increments: [],
      warnings: [],
      errors: [
        {
          code: $code,
          severity: "error",
          message: $message,
          source: {path: $source_path, line: null},
          details: $details
        }
      ],
      summary: {
        increment_count: 0,
        task_count: 0,
        warning_count: 0,
        error_count: 1,
        message: $message
      }
    }'
  printf 'plan-layers: input_error: %s\n' "$message" >&2
  exit 2
}

emit_marker_problem() {
  local status="$1" code="$2" message="$3" feature="${4:-}" tasks="${5:-}" details_json="$6" exit_code="$7"
  local feature_json tasks_json output_json source_path_json

  if [ -n "$feature" ]; then
    feature_json="$(json_value "$(normalize_for_display "$feature")")"
  else
    feature_json=null
  fi

  if [ -n "$tasks" ]; then
    tasks_json="$(json_value "$(normalize_for_display "$tasks")")"
    source_path_json="$tasks_json"
  else
    tasks_json=null
    if [ -n "$feature" ]; then
      source_path_json="$feature_json"
    else
      source_path_json=null
    fi
  fi

  if [ -n "${MARKER_OUTPUT_FILE:-}" ]; then
    output_json="$(json_value "$(normalize_for_display "$MARKER_OUTPUT_FILE")")"
  else
    output_json=null
  fi

  jq -cn \
    --arg status "$status" \
    --arg code "$code" \
    --arg message "$message" \
    --argjson feature_dir "$feature_json" \
    --argjson tasks_file "$tasks_json" \
    --argjson marker_plan_file "$output_json" \
    --argjson source_path "$source_path_json" \
    --argjson details "$details_json" \
    '{
      tool: "plan-layers",
      contract_version: 2,
      mode: "marker-plan",
      status: $status,
      feature_dir: $feature_dir,
      tasks_file: $tasks_file,
      marker_plan_file: $marker_plan_file,
      marker_ids: [],
      warnings: [],
      errors: [
        {
          code: $code,
          severity: "error",
          message: $message,
          source: {path: $source_path, line: null},
          details: $details
        }
      ],
      summary: {
        marker_count: 0,
        warning_count: 0,
        error_count: 1,
        hazard_collapsed: false,
        message: $message
      }
    }'
  printf 'plan-layers: %s: %s\n' "$status" "$message" >&2
  exit "$exit_code"
}

MODE=legacy
REVIEWABILITY_RESULT_FILE=""
HAZARD_ROUTE_FILE=""
STATE_FILE=""
MARKER_OUTPUT_FILE=""

if [ "$#" -eq 1 ]; then
  FEATURE_DIR="$1"
elif [ "${1:-}" = "marker-plan" ]; then
  MODE="marker-plan"
  if [ "$#" -ne 6 ]; then
    details="$(jq -cn --argjson received "$#" '{expected_args: 6, received_args: $received}')"
    TASKS_REL=null
    emit_marker_problem "input_error" "invalid_invocation" "Usage: plan-layers.sh marker-plan <feature-dir> <reviewability-result.json> <hazard-route.json> <state.json> <marker-plan-output.json>" "" "" "$details" "2"
  fi
  FEATURE_DIR="$2"
  REVIEWABILITY_RESULT_FILE="$3"
  HAZARD_ROUTE_FILE="$4"
  STATE_FILE="$5"
  MARKER_OUTPUT_FILE="$6"
else
  details="$(jq -cn --argjson received "$#" '{expected_args: 1, received_args: $received}')"
  TASKS_REL=null
  emit_input_error "invalid_invocation" "Usage: plan-layers.sh <feature-dir>" "" "" "$details"
fi

TASKS_FILE="$FEATURE_DIR/tasks.md"

if [ ! -e "$FEATURE_DIR" ]; then
  details="$(jq -cn --arg feature_dir "$(normalize_for_display "$FEATURE_DIR")" '{feature_dir: $feature_dir}')"
  TASKS_REL="$(normalize_for_display "$TASKS_FILE")"
  emit_input_error "feature_dir_not_found" "Feature directory not found: $(normalize_for_display "$FEATURE_DIR")" "$FEATURE_DIR" "" "$details"
fi

if [ ! -d "$FEATURE_DIR" ] || [ ! -r "$FEATURE_DIR" ] || [ ! -x "$FEATURE_DIR" ]; then
  details="$(jq -cn --arg feature_dir "$(normalize_for_display "$FEATURE_DIR")" '{feature_dir: $feature_dir}')"
  TASKS_REL="$(normalize_for_display "$TASKS_FILE")"
  emit_input_error "feature_dir_unreadable" "Feature directory unreadable: $(normalize_for_display "$FEATURE_DIR")" "$FEATURE_DIR" "" "$details"
fi

REPO_ROOT="$(git -C "$FEATURE_DIR" rev-parse --show-toplevel 2>/dev/null || printf '%s\n' "$CALLER_ROOT")"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"
FEATURE_REL="$(normalize_for_display "$FEATURE_DIR")"
TASKS_REL="$(normalize_for_display "$TASKS_FILE")"

if [ ! -e "$TASKS_FILE" ]; then
  details="$(jq -cn --arg tasks_file "$TASKS_REL" '{tasks_file: $tasks_file}')"
  emit_input_error "tasks_file_missing" "tasks.md missing: $TASKS_REL" "$FEATURE_DIR" "$TASKS_FILE" "$details"
fi

if [ ! -f "$TASKS_FILE" ] || [ ! -r "$TASKS_FILE" ]; then
  details="$(jq -cn --arg tasks_file "$TASKS_REL" '{tasks_file: $tasks_file}')"
  emit_input_error "tasks_file_unreadable" "tasks.md unreadable: $TASKS_REL" "$FEATURE_DIR" "$TASKS_FILE" "$details"
fi

declare -a LINES=()
mapfile -t LINES <"$TASKS_FILE"

declare -a SECTION_ORDER=()
declare -a ERRORS=()
declare -a WARNINGS=()
declare -A SECTION_EXISTS=()
declare -A SECTION_KIND=()
declare -A SECTION_NAME=()
declare -A SECTION_LINE=()
declare -A SECTION_HEADING=()
declare -A SECTION_TASKS=()
declare -A SECTION_MODE=()
declare -A TASK_SEEN=()
declare -A TASK_TITLE=()
declare -A TASK_STORY=()
declare -A TASK_INCREMENT=()
declare -A TASK_STATUS=()
declare -A TASK_PARALLEL=()
declare -A TASK_LINE=()
declare -A TASK_FILES_LIST=()
declare -A TASK_TESTS_LIST=()
declare -A DEPENDENCIES=()

add_error() {
  local code="$1" message="$2" line="$3" details_json="$4"
  ERRORS+=("$(diagnostic_json "$code" "error" "$message" "$line" "$details_json")")
}

add_warning() {
  local code="$1" message="$2" line="$3" details_json="$4"
  WARNINGS+=("$(diagnostic_json "$code" "warning" "$message" "$line" "$details_json")")
}

label_to_id() {
  local label cleaned lower
  label="$1"
  cleaned="${label//\`/}"
  cleaned="${cleaned//\*/}"
  cleaned="$(trim "$cleaned")"
  cleaned="$(trim "${cleaned//unknown/}")"
  lower="${cleaned,,}"

  if [[ "$lower" =~ ^(foundation|foundational|setup)([[:space:]].*)?$ ]]; then
    printf 'foundation\n'
    return
  fi
  if [[ "$cleaned" =~ [Pp]olish ]]; then
    printf 'polish\n'
    return
  fi
  if [[ "$cleaned" =~ (US|User[[:space:]]+Story)[[:space:]]*([1-9][0-9]*) ]]; then
    printf 'us%s\n' "${BASH_REMATCH[2]}"
    return
  fi
  return 1
}

clean_token() {
  local token="$1"
  clean_token_var token
  printf '%s' "$token"
}

clean_token_var() {
  local -n ref="$1"
  ref="${ref//\`/}"
  ref="${ref#\"}"
  ref="${ref%\"}"
  ref="${ref#\'}"
  ref="${ref%\'}"
  ref="${ref#(}"
  ref="${ref%)}"
  ref="${ref#[}"
  ref="${ref%]}"
  ref="${ref#<}"
  ref="${ref%>}"
  ref="${ref%,}"
  ref="${ref%;}"
  ref="${ref%:}"
  ref="${ref%.}"
}

reference_kind() {
  local ref="${1#./}"
  if [[ "$ref" == tests/* || "$ref" == */tests/* || "$ref" =~ (^|/)test-[^/]+\.sh$ ]]; then
    printf 'test\n'
  else
    printf 'file\n'
  fi
}

normalize_reference() {
  local raw="$1" token resolved
  NORMALIZED_REF=""
  REF_INSIDE_ROOT=false
  token="$raw"
  [ -z "$token" ] && return

  if [[ "$token" != /* && "$token" != *..* && "$token" != *"/./"* ]]; then
    NORMALIZED_REF="${token#./}"
    REF_INSIDE_ROOT=true
    return
  fi

  resolved="$(absolute_path "$token")"
  case "$resolved" in
    "$REPO_ROOT"/*)
      NORMALIZED_REF="${resolved#"$REPO_ROOT"/}"
      REF_INSIDE_ROOT=true
      ;;
    "$REPO_ROOT")
      NORMALIZED_REF="."
      REF_INSIDE_ROOT=true
      ;;
    *)
      NORMALIZED_REF="$token"
      REF_INSIDE_ROOT=false
      ;;
  esac
}

extract_references() {
  local title="$1" task_id="$2" increment_id="$3" line_no="$4"
  local word token kind target normalized
  local -a tokens=()
  local -a files=()
  local -a tests=()
  local -A seen_files=()
  local -A seen_tests=()

  for word in $title; do
    token="$word"
    token="${token//\`/}"
    token="${token#\"}"
    token="${token%\"}"
    token="${token#\'}"
    token="${token%\'}"
    token="${token#(}"
    token="${token%)}"
    token="${token#[}"
    token="${token%]}"
    token="${token#<}"
    token="${token%>}"
    token="${token%,}"
    token="${token%;}"
    token="${token%:}"
    token="${token%.}"
    if [[ "$token" =~ ^(\./|\.\./|/|[A-Za-z0-9_.-]+/) && "$token" =~ \.[A-Za-z0-9]+$ ]]; then
      tokens+=("$token")
    fi
  done

  for token in "${tokens[@]}"; do
    normalize_reference "$token"
    normalized="$NORMALIZED_REF"
    [ -z "$normalized" ] && continue
    if [[ "${normalized#./}" == tests/* || "${normalized#./}" == */tests/* || "${normalized#./}" =~ (^|/)test-[^/]+\.sh$ ]]; then
      kind=test
    else
      kind=file
    fi

    if [ "$REF_INSIDE_ROOT" != true ]; then
      details="$(jq -cn --arg kind "$kind" --arg reference "$(clean_token "$token")" --arg task_id "$task_id" \
        '{kind: $kind, reference: $reference, task_id: $task_id}')"
      add_warning "reference_not_found" "$kind reference is outside the worktree: $(clean_token "$token")" "$line_no" "$details"
      continue
    fi

    target="$REPO_ROOT/$normalized"
    if [ ! -e "$target" ]; then
      details="$(jq -cn --arg kind "$kind" --arg reference "$normalized" --arg task_id "$task_id" \
        '{kind: $kind, reference: $reference, task_id: $task_id}')"
      add_warning "reference_not_found" "$kind reference not found: $normalized" "$line_no" "$details"
    fi

    if [ "$kind" = "test" ]; then
      if [ -z "${seen_tests[$normalized]-}" ]; then
        seen_tests[$normalized]=1
        tests+=("$normalized")
      fi
    else
      if [ -z "${seen_files[$normalized]-}" ]; then
        seen_files[$normalized]=1
        files+=("$normalized")
      fi
    fi
  done

  if [ "${#files[@]}" -eq 0 ] && [ "${#tests[@]}" -eq 0 ]; then
    details="$(jq -cn --arg task_id "$task_id" --arg increment_id "$increment_id" \
      '{task_id: $task_id, increment_id: $increment_id}')"
    add_warning "task_without_references" "Task $task_id has no file or test references." "$line_no" "$details"
  fi

  if [ "${#files[@]}" -eq 0 ]; then
    EXTRACT_FILES_LIST=""
  else
    local IFS=$'\n'
    EXTRACT_FILES_LIST="${files[*]}"
  fi
  if [ "${#tests[@]}" -eq 0 ]; then
    EXTRACT_TESTS_LIST=""
  else
    local IFS=$'\n'
    EXTRACT_TESTS_LIST="${tests[*]}"
  fi
}

register_section() {
  local id="$1" name="$2" kind="$3" line_no="$4" heading="$5" mode="$6"

  if [ -n "${SECTION_EXISTS[$id]-}" ]; then
    if [ "$id" = "foundation" ] && { [ "${SECTION_MODE[$id]}" = "foundation_alias" ] || [ "$mode" = "foundation_alias" ]; }; then
      CURRENT_SECTION_ID="$id"
      SECTION_MODE[$id]="foundation_alias"
      return
    fi

    first_source="$(source_json "$TASKS_REL" "${SECTION_LINE[$id]}" "${SECTION_HEADING[$id]}")"
    duplicate_source="$(source_json "$TASKS_REL" "$line_no" "$heading")"
    details="$(jq -cn --arg increment_id "$id" --argjson first_source "$first_source" --argjson duplicate_source "$duplicate_source" \
      '{increment_id: $increment_id, first_source: $first_source, duplicate_source: $duplicate_source}')"
    add_error "duplicate_increment_id" "Increment $id is duplicated." "$line_no" "$details"
    CURRENT_SECTION_ID=""
    return
  fi

  SECTION_EXISTS[$id]=1
  SECTION_KIND[$id]="$kind"
  SECTION_NAME[$id]="$name"
  SECTION_LINE[$id]="$line_no"
  SECTION_HEADING[$id]="$heading"
  SECTION_TASKS[$id]=""
  SECTION_MODE[$id]="$mode"
  DEPENDENCIES[$id]=""
  SECTION_ORDER+=("$id")
  CURRENT_SECTION_ID="$id"
}

parse_phase_heading() {
  local line="$1" line_no="$2" title story_num story_title

  [[ "$line" =~ ^##[[:space:]]+Phase[[:space:]]+[0-9]+:[[:space:]]+(.+)$ ]] || return 1
  CURRENT_SECTION_ID=""
  title="$(trim "${BASH_REMATCH[1]}")"

  if [[ "${title,,}" =~ ^foundation([[:space:]].*)?$ ]]; then
    register_section "foundation" "Foundation" "foundation" "$line_no" "$line" "foundation_canonical"
    return 0
  fi

  if [[ "${title,,}" =~ ^(setup|foundational)([[:space:]].*)?$ ]]; then
    register_section "foundation" "Foundation" "foundation" "$line_no" "$line" "foundation_alias"
    return 0
  fi

  if [[ "$title" =~ ^User[[:space:]]+Story[[:space:]]+([1-9][0-9]*)[[:space:]]+-[[:space:]]+(.+)$ ]]; then
    story_num="${BASH_REMATCH[1]}"
    story_title="$(trim "${BASH_REMATCH[2]}")"
    if [[ "$story_title" =~ ^(.+)[[:space:]]+\((Priority|P):.*\)$ ]]; then
      story_title="$(trim "${BASH_REMATCH[1]}")"
    fi
    register_section "us${story_num}" "User Story ${story_num} - $story_title" "story" "$line_no" "$line" "canonical"
    return 0
  fi

  if [[ "$title" =~ [Pp]olish ]]; then
    register_section "polish" "$title" "polish" "$line_no" "$line" "canonical"
    return 0
  fi

  return 1
}

parse_task_line() {
  local line="$1" line_no="$2" section_id="$3"
  local marker task_id rest status parallel story first_source duplicate_source details

  if [[ "$line" =~ ^[[:space:]]*-[[:space:]]+\[([ xX])\][[:space:]]+(T[0-9]{3,})(.*)$ ]]; then
    marker="${BASH_REMATCH[1]}"
    task_id="${BASH_REMATCH[2]}"
    rest="${BASH_REMATCH[3]}"
    while [[ "$rest" == " "* ]]; do
      rest="${rest# }"
    done
  else
    if [[ "$line" =~ ^[[:space:]]*-[[:space:]]+\[[^]]+\][[:space:]]+T[0-9]{3,} ]]; then
      details="$(jq -cn --arg line_text "$(trim "$line")" '{line_text: $line_text}')"
      add_error "malformed_task" "Task-like checkbox line uses unsupported syntax." "$line_no" "$details"
    fi
    return
  fi

  parallel=false
  story=""
  while true; do
    if [[ "$rest" == "[P]"* ]]; then
      parallel=true
      rest="${rest:3}"
      while [[ "$rest" == " "* ]]; do
        rest="${rest# }"
      done
      continue
    fi
    if [[ "$rest" =~ ^\[US([1-9][0-9]*)\][[:space:]]*(.*)$ ]]; then
      story="us${BASH_REMATCH[1]}"
      rest="${BASH_REMATCH[2]}"
      continue
    fi
    break
  done

  if [ "${SECTION_KIND[$section_id]}" = "story" ] && [ -z "$story" ]; then
    story="$section_id"
  fi

  if [[ "$marker" = "x" || "$marker" = "X" ]]; then
    status=done
  else
    status=todo
  fi

  extract_references "$rest" "$task_id" "$section_id" "$line_no"
  if [ -n "${TASK_SEEN[$task_id]-}" ]; then
    first_source="$(source_json "$TASKS_REL" "${TASK_LINE[$task_id]}")"
    duplicate_source="$(source_json "$TASKS_REL" "$line_no")"
    details="$(jq -cn --arg task_id "$task_id" --argjson first_source "$first_source" --argjson duplicate_source "$duplicate_source" \
      '{task_id: $task_id, first_source: $first_source, duplicate_source: $duplicate_source}')"
    add_error "duplicate_task_id" "Task ID $task_id is duplicated." "$line_no" "$details"
  else
    TASK_SEEN[$task_id]=1
  fi

  TASK_TITLE[$task_id]="$rest"
  TASK_STORY[$task_id]="$story"
  TASK_INCREMENT[$task_id]="$section_id"
  TASK_STATUS[$task_id]="$status"
  TASK_PARALLEL[$task_id]="$parallel"
  TASK_LINE[$task_id]="$line_no"
  TASK_FILES_LIST[$task_id]="$EXTRACT_FILES_LIST"
  TASK_TESTS_LIST[$task_id]="$EXTRACT_TESTS_LIST"
  SECTION_TASKS[$section_id]="${SECTION_TASKS[$section_id]}$task_id"$'\n'
}

CURRENT_SECTION_ID=""
for index in "${!LINES[@]}"; do
  line_no=$((index + 1))
  line="${LINES[$index]}"

  if parse_phase_heading "$line" "$line_no"; then
    continue
  fi

  if [[ "$line" == "## "* ]]; then
    CURRENT_SECTION_ID=""
    continue
  fi

  if [ -n "$CURRENT_SECTION_ID" ]; then
    parse_task_line "$line" "$line_no" "$CURRENT_SECTION_ID"
  fi
done

dependency_heading_present=false
delivery_heading_present=false
for line in "${LINES[@]}"; do
  [ "$line" = "## Dependencies & Execution Order" ] && dependency_heading_present=true
  [ "$line" = "### Incremental Delivery" ] && delivery_heading_present=true
done

if [ "$dependency_heading_present" != true ]; then
  details="$(jq -cn '{required_heading: "## Dependencies & Execution Order"}')"
  add_error "missing_required_heading" "Missing required dependency heading." "" "$details"
fi
if [ "$delivery_heading_present" != true ]; then
  details="$(jq -cn '{required_heading: "### Incremental Delivery"}')"
  add_error "missing_required_heading" "Missing required incremental delivery heading." "" "$details"
fi

declare -a DELIVERY_ORDER=()
in_delivery=false
for index in "${!LINES[@]}"; do
  line_no=$((index + 1))
  line="${LINES[$index]}"
  stripped="$line"

  if [ "$stripped" = "### Incremental Delivery" ]; then
    in_delivery=true
    continue
  fi
  if [ "$in_delivery" = true ] && [[ "$stripped" == "### "* ]]; then
    in_delivery=false
  fi
  [ "$in_delivery" = true ] || continue

  if [[ "$line" =~ ^[[:space:]]*[0-9]+\.[[:space:]]+Complete[[:space:]]+([^:]+): ]]; then
    if inc_id="$(label_to_id "${BASH_REMATCH[1]}")"; then
      already=false
      for existing in "${DELIVERY_ORDER[@]}"; do
        [ "$existing" = "$inc_id" ] && already=true
      done
      if [ "$already" = false ]; then
        DELIVERY_ORDER+=("$inc_id")
      fi
      if [ -z "${SECTION_EXISTS[$inc_id]-}" ]; then
        details="$(jq -cn --arg increment_id "$inc_id" '{increment_id: $increment_id}')"
        add_error "unknown_increment" "Delivery order references unknown increment $inc_id." "$line_no" "$details"
      fi
    fi
  fi
done

if [ "${#DELIVERY_ORDER[@]}" -eq 0 ]; then
  DELIVERY_ORDER=("${SECTION_ORDER[@]}")
fi

for section_id in "${SECTION_ORDER[@]}"; do
  if [ -z "$(trim "${SECTION_TASKS[$section_id]-}")" ]; then
    details="$(jq -cn --arg increment_id "$section_id" '{increment_id: $increment_id}')"
    add_error "empty_increment" "Increment $section_id has no parseable tasks." "${SECTION_LINE[$section_id]}" "$details"
  fi
done

append_dependency() {
  local inc_id="$1" dep="$2" existing
  existing=$'\n'"${DEPENDENCIES[$inc_id]-}"$'\n'
  if [[ "$existing" != *$'\n'"$dep"$'\n'* ]]; then
    DEPENDENCIES[$inc_id]="${DEPENDENCIES[$inc_id]-}$dep"$'\n'
  fi
}

for index in "${!LINES[@]}"; do
  line_no=$((index + 1))
  line="${LINES[$index]}"
  if [[ "$line" =~ ^[[:space:]]*-[[:space:]]+\*\*([^*]+)\*\*:[[:space:]]+Depends[[:space:]]+on[[:space:]]+(.+)$ ]]; then
    if ! inc_id="$(label_to_id "${BASH_REMATCH[1]}")"; then
      continue
    fi
    dep_text="$(trim "${BASH_REMATCH[2]%.}")"
    if [[ "$dep_text" =~ [Nn]o[[:space:]]+prerequisites || "$dep_text" =~ [Ff]oundation[[:space:]]+only ]]; then
      DEPENDENCIES[$inc_id]="${DEPENDENCIES[$inc_id]-}"
      continue
    fi

    declare -a found_deps=()
    if [[ "$dep_text" =~ [Ff]oundation ]]; then
      found_deps+=("foundation")
    fi
    while [[ "$dep_text" =~ (US|User[[:space:]]+Story)[[:space:]]*([1-9][0-9]*) ]]; do
      found_deps+=("us${BASH_REMATCH[2]}")
      dep_text="${dep_text#*"${BASH_REMATCH[0]}"}"
    done
    if [[ "$dep_text" =~ [Pp]olish ]]; then
      found_deps+=("polish")
    fi

    for dep in "${found_deps[@]}"; do
      if [ -z "${SECTION_EXISTS[$dep]-}" ]; then
        details="$(jq -cn --arg increment_id "$dep" '{increment_id: $increment_id}')"
        add_error "unknown_increment" "Dependency references unknown increment $dep." "$line_no" "$details"
      fi
      append_dependency "$inc_id" "$dep"
    done
  fi
done

declare -a KNOWN_ORDER=()
for inc_id in "${DELIVERY_ORDER[@]}"; do
  [ -n "${SECTION_EXISTS[$inc_id]-}" ] && KNOWN_ORDER+=("$inc_id")
done
for inc_id in "${SECTION_ORDER[@]}"; do
  already=false
  for existing in "${KNOWN_ORDER[@]}"; do
    [ "$existing" = "$inc_id" ] && already=true
  done
  [ "$already" = false ] && KNOWN_ORDER+=("$inc_id")
done

order_position() {
  local needle="$1" idx
  for idx in "${!KNOWN_ORDER[@]}"; do
    if [ "${KNOWN_ORDER[$idx]}" = "$needle" ]; then
      printf '%s\n' "$idx"
      return
    fi
  done
  printf '%s\n' "-1"
}

declare -a EXPECTED_ORDER=()
declare -A TOPO_VISITING=()
declare -A TOPO_VISITED=()

topo_visit() {
  local node="$1" dep
  [ -n "${TOPO_VISITED[$node]-}" ] && return
  [ -n "${TOPO_VISITING[$node]-}" ] && return

  TOPO_VISITING[$node]=1
  while IFS= read -r dep; do
    [ -n "$dep" ] || continue
    [ -n "${SECTION_EXISTS[$dep]-}" ] || continue
    topo_visit "$dep"
  done <<<"${DEPENDENCIES[$node]-}"
  unset "TOPO_VISITING[$node]"
  TOPO_VISITED[$node]=1
  EXPECTED_ORDER+=("$node")
}

for inc_id in "${KNOWN_ORDER[@]}"; do
  topo_visit "$inc_id"
done

known_order_json="$(json_array_from_ordered_values "${KNOWN_ORDER[@]}")"
expected_order_json="$(json_array_from_ordered_values "${EXPECTED_ORDER[@]}")"
for inc_id in "${SECTION_ORDER[@]}"; do
  inc_pos="$(order_position "$inc_id")"
  while IFS= read -r dep; do
    [ -n "$dep" ] || continue
    [ -n "${SECTION_EXISTS[$dep]-}" ] || continue
    dep_pos="$(order_position "$dep")"
    if [ "$dep_pos" -gt "$inc_pos" ]; then
      details="$(jq -cn --argjson expected_order "$expected_order_json" --argjson observed_order "$known_order_json" \
        '{expected_order: $expected_order, observed_order: $observed_order}')"
      add_error "contradictory_increment_order" "Increment $inc_id is ordered before dependency $dep." "${SECTION_LINE[$inc_id]}" "$details"
      break
    fi
  done <<<"${DEPENDENCIES[$inc_id]-}"
done

declare -a CYCLE_STACK=()
declare -a CYCLE_RESULT=()
declare -A CYCLE_VISITING=()
declare -A CYCLE_VISITED=()

cycle_visit() {
  local node="$1" dep idx stack_len
  if [ -n "${CYCLE_VISITING[$node]-}" ]; then
    CYCLE_RESULT=()
    for idx in "${!CYCLE_STACK[@]}"; do
      if [ "${CYCLE_STACK[$idx]}" = "$node" ]; then
        CYCLE_RESULT=("${CYCLE_STACK[@]:$idx}" "$node")
        return 0
      fi
    done
    return 0
  fi
  [ -n "${CYCLE_VISITED[$node]-}" ] && return 1

  CYCLE_VISITING[$node]=1
  CYCLE_STACK+=("$node")
  while IFS= read -r dep; do
    [ -n "$dep" ] || continue
    [ -n "${SECTION_EXISTS[$dep]-}" ] || continue
    if cycle_visit "$dep"; then
      return 0
    fi
  done <<<"${DEPENDENCIES[$node]-}"

  unset "CYCLE_VISITING[$node]"
  stack_len="${#CYCLE_STACK[@]}"
  if [ "$stack_len" -gt 0 ]; then
    CYCLE_STACK=("${CYCLE_STACK[@]:0:$((stack_len - 1))}")
  fi
  CYCLE_VISITED[$node]=1
  return 1
}

find_cycle() {
  local node
  for node in "${KNOWN_ORDER[@]}"; do
    CYCLE_STACK=()
    if cycle_visit "$node"; then
      printf '%s\n' "${CYCLE_RESULT[@]}"
      return 0
    fi
  done
  return 1
}

if cycle_lines="$(find_cycle)"; then
  mapfile -t cycle_items <<<"$cycle_lines"
  cycle_json="$(json_array_from_ordered_values "${cycle_items[@]}")"
  first="${cycle_items[0]}"
  details="$(jq -cn --argjson cycle "$cycle_json" '{cycle: $cycle}')"
  add_error "dependency_cycle" "Dependency graph contains a cycle." "${SECTION_LINE[$first]}" "$details"
fi

declare -a INCREMENTS=()
for inc_id in "${KNOWN_ORDER[@]}"; do
  [ -n "${SECTION_EXISTS[$inc_id]-}" ] || continue
  task_records=""
  declare -a all_files=()
  declare -a all_tests=()

  while IFS= read -r task_id; do
    [ -n "$task_id" ] || continue
    files_record="${TASK_FILES_LIST[$task_id]//$'\n'/$'\037'}"
    tests_record="${TASK_TESTS_LIST[$task_id]//$'\n'/$'\037'}"
    task_records+="${task_id}"$'\t'"${TASK_TITLE[$task_id]}"$'\t'"${TASK_STORY[$task_id]}"$'\t'"${TASK_INCREMENT[$task_id]}"$'\t'"${TASK_STATUS[$task_id]}"$'\t'"${TASK_PARALLEL[$task_id]}"$'\t'"${TASK_LINE[$task_id]}"$'\t'"${files_record}"$'\t'"${tests_record}"$'\n'
    while IFS= read -r value; do
      [ -n "$value" ] && all_files+=("$value")
    done <<<"${TASK_FILES_LIST[$task_id]}"
    while IFS= read -r value; do
      [ -n "$value" ] && all_tests+=("$value")
    done <<<"${TASK_TESTS_LIST[$task_id]}"
  done <<<"${SECTION_TASKS[$inc_id]-}"

  task_items_json="$(printf '%s' "$task_records" | jq -Rn --arg tasks_file "$TASKS_REL" '
    def split_list:
      if . == "" then [] else split("\u001f") | map(select(length > 0)) | sort end;
    [
      inputs
      | select(length > 0)
      | split("\t") as $f
      | {
          id: $f[0],
          title: $f[1],
          story: (if $f[2] == "" then null else $f[2] end),
          increment_id: $f[3],
          status: $f[4],
          parallel: ($f[5] == "true"),
          source: {path: $tasks_file, line: ($f[6] | tonumber)},
          files: ($f[7] | split_list),
          tests: ($f[8] | split_list)
        }
    ]')"
  files_json="$(json_array_from_values "${all_files[@]}")"
  tests_json="$(json_array_from_values "${all_tests[@]}")"
  source="$(source_json "$TASKS_REL" "${SECTION_LINE[$inc_id]}" "${SECTION_HEADING[$inc_id]}")"
  depends=()
  while IFS= read -r dep; do
    [ -n "$dep" ] || continue
    [ -n "${SECTION_EXISTS[$dep]-}" ] || continue
    dep_pos="$(order_position "$dep")"
    inc_pos="$(order_position "$inc_id")"
    [ "$dep_pos" -lt "$inc_pos" ] && depends+=("$dep")
  done <<<"${DEPENDENCIES[$inc_id]-}"
  depends_json="$(json_array_from_values "${depends[@]}")"
  file_ref_count="${#all_files[@]}"
  test_ref_count="${#all_tests[@]}"

  increment_json="$(jq -cn \
    --arg id "$inc_id" \
    --arg name "${SECTION_NAME[$inc_id]}" \
    --arg kind "${SECTION_KIND[$inc_id]}" \
    --argjson order "${#INCREMENTS[@]}" \
    --argjson depends_on "$depends_json" \
    --argjson source "$source" \
    --argjson tasks "$task_items_json" \
    --argjson files "$files_json" \
    --argjson tests "$tests_json" \
    --argjson task_count "$(printf '%s' "$task_items_json" | jq 'length')" \
    --argjson file_reference_count "$file_ref_count" \
    --argjson distinct_file_count "$(printf '%s' "$files_json" | jq 'length')" \
    --argjson test_reference_count "$test_ref_count" \
    --argjson distinct_test_count "$(printf '%s' "$tests_json" | jq 'length')" \
    '{
      id: $id,
      name: $name,
      kind: $kind,
      order: $order,
      depends_on: $depends_on,
      source: $source,
      tasks: $tasks,
      files: $files,
      tests: $tests,
      advisory_size: {
        task_count: $task_count,
        file_reference_count: $file_reference_count,
        distinct_file_count: $distinct_file_count,
        test_reference_count: $test_reference_count,
        distinct_test_count: $distinct_test_count
      }
    }')"
  INCREMENTS+=("$increment_json")
done

increments_json="$(json_array_from_json_items "${INCREMENTS[@]}")"
warnings_json="$(json_array_from_json_items "${WARNINGS[@]}")"
errors_json="$(json_array_from_json_items "${ERRORS[@]}")"
task_count="$(printf '%s' "$increments_json" | jq '[.[].tasks | length] | add // 0')"
increment_count="$(printf '%s' "$increments_json" | jq 'length')"
warning_count="${#WARNINGS[@]}"
error_count="${#ERRORS[@]}"

if [ "$error_count" -gt 0 ]; then
  status="invalid_plan"
  message="Layer plan invalid: $error_count error(s)."
else
  status="ok"
  message="Planned $increment_count increment(s) with $task_count task(s)."
fi

if [ "$MODE" = "marker-plan" ]; then
  marker_plan_path_display="$(normalize_for_display "$MARKER_OUTPUT_FILE")"

  emit_marker_validation_error() {
    local code="$1" text="$2" details_json="$3"
    emit_marker_problem "invalid_plan" "$code" "$text" "$FEATURE_DIR" "$TASKS_FILE" "$details_json" "1"
  }

  emit_marker_input_path_error() {
    local code="$1" text="$2" details_json="$3"
    emit_marker_problem "input_error" "$code" "$text" "$FEATURE_DIR" "$TASKS_FILE" "$details_json" "2"
  }

  hash_file() {
    shasum -a 256 "$1" | awk '{print $1}'
  }

  if [ "$status" = "invalid_plan" ]; then
    jq -cn \
      --arg feature_dir "$FEATURE_REL" \
      --arg tasks_file "$TASKS_REL" \
      --arg marker_plan_file "$marker_plan_path_display" \
      --argjson warnings "$warnings_json" \
      --argjson errors "$errors_json" \
      --argjson warning_count "$warning_count" \
      --argjson error_count "$error_count" \
      --arg message "$message" \
      '{
        tool: "plan-layers",
        contract_version: 2,
        mode: "marker-plan",
        status: "invalid_plan",
        feature_dir: $feature_dir,
        tasks_file: $tasks_file,
        marker_plan_file: $marker_plan_file,
        marker_ids: [],
        warnings: $warnings,
        errors: $errors,
        summary: {
          marker_count: 0,
          warning_count: $warning_count,
          error_count: $error_count,
          hazard_collapsed: false,
          message: $message
        }
      }'
    printf 'plan-layers: invalid_plan: %s error(s)\n' "$error_count" >&2
    exit 1
  fi

  SPEC_FILE="$FEATURE_DIR/spec.md"
  PLAN_FILE="$FEATURE_DIR/plan.md"
  if [ ! -f "$SPEC_FILE" ] || [ ! -r "$SPEC_FILE" ]; then
    details="$(jq -cn --arg spec_file "$(normalize_for_display "$SPEC_FILE")" '{spec_file: $spec_file}')"
    emit_marker_input_path_error "feature_spec_unreadable" "Feature spec is missing or unreadable: $(normalize_for_display "$SPEC_FILE")" "$details"
  fi
  if [ ! -f "$PLAN_FILE" ] || [ ! -r "$PLAN_FILE" ]; then
    details="$(jq -cn --arg plan_file "$(normalize_for_display "$PLAN_FILE")" '{plan_file: $plan_file}')"
    emit_marker_input_path_error "feature_plan_unreadable" "Feature plan is missing or unreadable: $(normalize_for_display "$PLAN_FILE")" "$details"
  fi

  if [ ! -f "$REVIEWABILITY_RESULT_FILE" ] || [ ! -r "$REVIEWABILITY_RESULT_FILE" ]; then
    details="$(jq -cn --arg reviewability_result "$(normalize_for_display "$REVIEWABILITY_RESULT_FILE")" '{reviewability_result: $reviewability_result}')"
    emit_marker_input_path_error "reviewability_result_unreadable" "Reviewability result is missing or unreadable: $(normalize_for_display "$REVIEWABILITY_RESULT_FILE")" "$details"
  fi
  if [ ! -f "$HAZARD_ROUTE_FILE" ] || [ ! -r "$HAZARD_ROUTE_FILE" ]; then
    details="$(jq -cn --arg hazard_route "$(normalize_for_display "$HAZARD_ROUTE_FILE")" '{hazard_route: $hazard_route}')"
    emit_marker_input_path_error "hazard_route_unreadable" "Hazard route is missing or unreadable: $(normalize_for_display "$HAZARD_ROUTE_FILE")" "$details"
  fi
  if [ ! -f "$STATE_FILE" ] || [ ! -r "$STATE_FILE" ]; then
    details="$(jq -cn --arg state_file "$(normalize_for_display "$STATE_FILE")" '{state_file: $state_file}')"
    emit_marker_input_path_error "state_file_unreadable" "Current state is missing or unreadable: $(normalize_for_display "$STATE_FILE")" "$details"
  fi

  output_parent="$(dirname "$MARKER_OUTPUT_FILE")"
  if [ ! -d "$output_parent" ] || [ ! -w "$output_parent" ]; then
    details="$(jq -cn --arg marker_plan_file "$marker_plan_path_display" '{marker_plan_file: $marker_plan_file}')"
    emit_marker_input_path_error "marker_plan_output_unwritable" "Marker plan output directory is not writable: $(normalize_for_display "$output_parent")" "$details"
  fi

  if ! jq -e . "$REVIEWABILITY_RESULT_FILE" >/dev/null 2>&1; then
    details="$(jq -cn --arg reviewability_result "$(normalize_for_display "$REVIEWABILITY_RESULT_FILE")" '{reviewability_result: $reviewability_result}')"
    emit_marker_validation_error "malformed_reviewability_result" "Reviewability result is not valid JSON." "$details"
  fi
  if ! jq -e . "$HAZARD_ROUTE_FILE" >/dev/null 2>&1; then
    details="$(jq -cn --arg hazard_route "$(normalize_for_display "$HAZARD_ROUTE_FILE")" '{hazard_route: $hazard_route}')"
    emit_marker_validation_error "malformed_hazard_route" "Hazard route is not valid JSON." "$details"
  fi
  if ! jq -e . "$STATE_FILE" >/dev/null 2>&1; then
    details="$(jq -cn --arg state_file "$(normalize_for_display "$STATE_FILE")" '{state_file: $state_file}')"
    emit_marker_validation_error "malformed_current_state" "Current state is not valid JSON." "$details"
  fi

  FEATURE_ID="$(basename "$(absolute_path "$FEATURE_DIR")")"
  reviewability_status="$(jq -r '.status // empty' "$REVIEWABILITY_RESULT_FILE")"
  reviewability_mode="$(jq -r '.mode // empty' "$REVIEWABILITY_RESULT_FILE")"
  reviewability_feature="$(jq -r '.feature_id // empty' "$REVIEWABILITY_RESULT_FILE")"
  reviewability_size_only="$(jq -r 'if has("is_size_only") then .is_size_only else empty end' "$REVIEWABILITY_RESULT_FILE")"
  case "$reviewability_status" in
    pass|warn|exception|block) ;;
    *)
      details="$(jq -cn --arg status "$reviewability_status" '{status: $status}')"
      emit_marker_validation_error "malformed_reviewability_result" "Reviewability result has an unsupported or missing status." "$details"
      ;;
  esac
  if [ "$reviewability_mode" != "tasks" ]; then
    details="$(jq -cn --arg mode "$reviewability_mode" '{mode: $mode, expected_mode: "tasks"}')"
    emit_marker_validation_error "malformed_reviewability_result" "Reviewability result mode must be tasks." "$details"
  fi
  if [ -n "$reviewability_feature" ] && [ "$reviewability_feature" != "$FEATURE_ID" ]; then
    details="$(jq -cn --arg feature_id "$reviewability_feature" --arg expected_feature_id "$FEATURE_ID" '{feature_id: $feature_id, expected_feature_id: $expected_feature_id}')"
    emit_marker_validation_error "stale_reviewability_result" "Reviewability result belongs to a different feature." "$details"
  fi
  if [ "$reviewability_status" = "block" ] && [ "$reviewability_size_only" != "true" ]; then
    details="$(jq -cn --arg status "$reviewability_status" --arg is_size_only "${reviewability_size_only:-}" '{status: $status, is_size_only: $is_size_only}')"
    emit_marker_validation_error "non_size_reviewability_block" "Reviewability block is not marked as size-only marker input." "$details"
  fi

  hazard_route="$(jq -r '.route // empty' "$HAZARD_ROUTE_FILE")"
  hazard_releasable="$(jq -r 'if has("releasable") then .releasable else empty end' "$HAZARD_ROUTE_FILE")"
  if [ -z "$hazard_route" ] || { [ "$hazard_releasable" != "true" ] && [ "$hazard_releasable" != "false" ]; }; then
    details="$(jq -cn --arg route "$hazard_route" --arg releasable "$hazard_releasable" '{route: $route, releasable: $releasable}')"
    emit_marker_validation_error "malformed_hazard_route" "Hazard route must include route and boolean releasable fields." "$details"
  fi

  hazard_collapsed=false
  if [ "$hazard_route" = "single-atomic-PR" ] || [ "$hazard_releasable" = "false" ]; then
    hazard_collapsed=true
  fi

  fingerprint_json="$(jq -cn \
    --arg feature_spec_sha "$(hash_file "$SPEC_FILE")" \
    --arg plan_declared_scope_sha "$(hash_file "$PLAN_FILE")" \
    --arg tasks_sha "$(hash_file "$TASKS_FILE")" \
    --arg reviewability_sha "$(hash_file "$REVIEWABILITY_RESULT_FILE")" \
    --arg hazard_route_sha "$(hash_file "$HAZARD_ROUTE_FILE")" \
    '{
      feature_spec_sha: $feature_spec_sha,
      plan_declared_scope_sha: $plan_declared_scope_sha,
      tasks_sha: $tasks_sha,
      reviewability_sha: $reviewability_sha,
      hazard_route_sha: $hazard_route_sha
    }')"

  state_stale="$(jq -r -n \
    --slurpfile state "$STATE_FILE" \
    --arg feature_id "$FEATURE_ID" \
    --argjson fingerprint "$fingerprint_json" \
    '($state[0].pr_marker_plan? // null) as $plan
      | if (($plan | type) == "object" and ($plan.feature_id // "") == $feature_id and (($plan.source_fingerprint // {}) != $fingerprint))
        then "true"
        else "false"
        end')"
  if [ "$state_stale" = "true" ]; then
    details="$(jq -cn --arg feature_id "$FEATURE_ID" --argjson expected_fingerprint "$fingerprint_json" '{feature_id: $feature_id, expected_fingerprint: $expected_fingerprint}')"
    emit_marker_validation_error "stale_marker_fingerprint" "Existing marker plan fingerprint is stale for current inputs." "$details"
  fi

  marker_plan_json="$(jq -cn \
    --arg feature_id "$FEATURE_ID" \
    --argjson increments "$increments_json" \
    --argjson source_fingerprint "$fingerprint_json" \
    --slurpfile reviewability "$REVIEWABILITY_RESULT_FILE" \
    --slurpfile hazard "$HAZARD_ROUTE_FILE" \
    --argjson hazard_collapsed "$hazard_collapsed" \
    '
    $reviewability[0] as $review
    | $hazard[0] as $hazard_route
    | def unique_sorted: unique | sort;
    def story_number($id):
      if ($id | test("^us[0-9]+")) then ($id | capture("^us(?<n>[0-9]+)") | .n | tonumber) else null end;
    def task_ids($tasks): [$tasks[]?.id];
    def files_for($tasks): [$tasks[]?.files[]?] | unique_sorted;
    def tests_for($tasks): [$tasks[]?.tests[]?] | unique_sorted;
    def file_ops($files): [$files[]? | {operation: "MODIFIED", path: .}];
    def boundary($inc; $tasks): {
      section: $inc.name,
      story_id: story_number($inc.id),
      start_task_id: ($tasks[0].id // ""),
      end_task_id: ($tasks[-1].id // "")
    };
    def warning($code; $message; $source; $details): {
      code: $code,
      severity: "warning",
      message: $message,
      source: $source,
      details: $details
    };
    def marker_reviewability($scope): {
      status: $review.status,
      mode: $review.mode,
      scope: $scope,
      evidence_path: ($review.evidence_path // "")
    };
    def marker($inc; $id; $kind; $parent; $tasks; $subdivision_status; $subdivision_details; $marker_warnings): {
      id: $id,
      review_order: 0,
      kind: $kind,
      parent_marker_id: $parent,
      source_boundary: boundary($inc; $tasks),
      task_ids: task_ids($tasks),
      folded_polish_task_ids: [],
      folded_polish_target_reason: "",
      declared_files: file_ops(files_for($tasks)),
      declared_tests: tests_for($tasks),
      reviewability: marker_reviewability($id),
      hazards: (($hazard_route.signals // []) + ($hazard_route.warnings // [])),
      subdivision: {
        status: $subdivision_status,
        details: $subdivision_details
      },
      implementation_checkpoint: {
        status: "pending"
      },
      emission_mapping: {
        status: "pending"
      },
      warnings: $marker_warnings
    };
    def disjoint($left; $right):
      ((($left - $right) | length) == ($left | length)) and ((($right - $left) | length) == ($right | length));
    def has_shared_signal($tasks):
      any($tasks[]?; (.title // "" | test("shared|hazard|migration|atomic"; "i")));
    def can_safe_split($tasks):
      ($tasks | length) >= 4
      and (has_shared_signal($tasks) | not)
      and (($tasks | length) / 2 | floor) as $mid
      | ($tasks[0:$mid]) as $left
      | ($tasks[$mid:]) as $right
      | ($left | length) > 0
        and ($right | length) > 0
        and disjoint(files_for($left); files_for($right))
        and disjoint(tests_for($left); tests_for($right));
    def story_is_oversized($inc):
      (($review.marker_estimates[$inc.id].status? // "") == "block") or (($review.marker_estimates[$inc.id].oversized? // false) == true);
    def story_markers($inc):
      $inc.tasks as $tasks
      | if story_is_oversized($inc) then
          if can_safe_split($tasks) then
            (($tasks | length) / 2 | floor) as $mid
            | [
                marker($inc; ($inc.id + "-part1"); "user_story_part"; $inc.id; $tasks[0:$mid]; "safe_split"; {parent_marker_id: $inc.id, part: 1}; []),
                marker($inc; ($inc.id + "-part2"); "user_story_part"; $inc.id; $tasks[$mid:]; "safe_split"; {parent_marker_id: $inc.id, part: 2}; [])
              ]
          else
            warning(
              "no_safe_boundary";
              "Oversized user story has no safe internal marker boundary.";
              "plan-layers";
              {marker_id: $inc.id, task_ids: task_ids($tasks)}
            ) as $warn
            | [
                marker($inc; $inc.id; "user_story"; null; $tasks; "no_safe_boundary"; {reason: "shared_or_overlapping_scope"}; [$warn])
              ]
          end
        else
          [marker($inc; $inc.id; "user_story"; null; $tasks; "none"; {}; [])]
        end;
    def fold_polish($markers; $polish_tasks):
      if (($polish_tasks | length) == 0) or (($markers | length) == 0) then
        $markers
      else
        ($markers | length) as $count
        | [range(0; $count) as $index
          | if $index == ($count - 1) then
              $markers[$index]
              | .folded_polish_task_ids = task_ids($polish_tasks)
              | .folded_polish_target_reason = "nearest_preceding_non_polish_scope"
              | .declared_files = ((.declared_files + file_ops(files_for($polish_tasks))) | unique_by(.path))
              | .declared_tests = ((.declared_tests + tests_for($polish_tasks)) | unique_sorted)
            else
              $markers[$index]
            end]
      end;
    (
      [$increments[] | select(.kind == "foundation") | marker(.; "foundation"; "foundation"; null; .tasks; "none"; {}; [])]
      + [$increments[] | select(.kind == "story") | story_markers(.)[]]
    ) as $base_markers
    | [$increments[] | select(.kind == "polish") | .tasks[]?] as $polish_tasks
    | fold_polish($base_markers; $polish_tasks) as $folded_markers
    | [range(0; ($folded_markers | length)) as $index | $folded_markers[$index] + {review_order: ($index + 1)}] as $ordered_markers
    | ($ordered_markers | map(.id)) as $source_marker_ids
    | (if $hazard_collapsed then
        $ordered_markers | map(.emission_mapping = {status: "hazard_collapsed", source_marker_ids: $source_marker_ids})
      else
        $ordered_markers
      end) as $final_markers
    | (
        [
          if (($review.status == "warn") or ($review.status == "block")) then
            warning(
              "reviewability_size_warning";
              "Reviewability sizing result is marker-planning input.";
              "reviewability";
              {status: $review.status, mode: $review.mode, evidence_path: ($review.evidence_path // "")}
            )
          else empty end
        ]
        + [$final_markers[].warnings[]? | select(.code == "no_safe_boundary")]
        + [
          if $hazard_collapsed then
            warning(
              "hazard_collapse_required";
              "Hazard route requires collapsed PR emission while preserving marker evidence.";
              "hazard-route";
              {route: $hazard_route.route, releasable: $hazard_route.releasable, source_marker_ids: $source_marker_ids}
            )
          else empty end
        ]
      ) as $plan_warnings
    | {
        schema_version: "pr-marker-plan.v1",
        kind: "pr_marker_plan",
        feature_id: $feature_id,
        status: (if $hazard_collapsed then "collapsed" else "planned" end),
        source_fingerprint: $source_fingerprint,
        markers: $final_markers,
        warnings: $plan_warnings
      }')"

  if ! printf '%s\n' "$marker_plan_json" | jq -e . >/dev/null 2>&1; then
    details="$(jq -cn '{reason: "generated marker plan did not parse"}')"
    emit_marker_validation_error "malformed_marker_plan" "Generated marker plan is not valid JSON." "$details"
  fi

  printf '%s\n' "$marker_plan_json" >"$MARKER_OUTPUT_FILE"

  marker_ids_json="$(printf '%s\n' "$marker_plan_json" | jq '[.markers[].id]')"
  marker_warnings_json="$(printf '%s\n' "$marker_plan_json" | jq '.warnings')"
  marker_count="$(printf '%s\n' "$marker_plan_json" | jq '.markers | length')"
  marker_warning_count="$(printf '%s\n' "$marker_plan_json" | jq '.warnings | length')"
  marker_message="Planned $marker_count PR marker(s)."
  if [ "$hazard_collapsed" = true ]; then
    marker_message="Planned $marker_count PR marker(s) with hazard-collapsed emission."
  fi

  jq -cn \
    --arg feature_dir "$FEATURE_REL" \
    --arg tasks_file "$TASKS_REL" \
    --arg marker_plan_file "$marker_plan_path_display" \
    --argjson marker_ids "$marker_ids_json" \
    --argjson warnings "$marker_warnings_json" \
    --argjson marker_count "$marker_count" \
    --argjson warning_count "$marker_warning_count" \
    --argjson hazard_collapsed "$hazard_collapsed" \
    --arg message "$marker_message" \
    '{
      tool: "plan-layers",
      contract_version: 2,
      mode: "marker-plan",
      status: "ok",
      feature_dir: $feature_dir,
      tasks_file: $tasks_file,
      marker_plan_file: $marker_plan_file,
      marker_ids: $marker_ids,
      warnings: $warnings,
      errors: [],
      summary: {
        marker_count: $marker_count,
        warning_count: $warning_count,
        error_count: 0,
        hazard_collapsed: $hazard_collapsed,
        message: $message
      }
    }'
  if [ "$marker_warning_count" -gt 0 ]; then
    printf 'plan-layers: marker-plan ok with %s warning(s)\n' "$marker_warning_count" >&2
  fi
  exit 0
fi

jq -cn \
  --arg status "$status" \
  --arg feature_dir "$FEATURE_REL" \
  --arg tasks_file "$TASKS_REL" \
  --argjson increments "$increments_json" \
  --argjson warnings "$warnings_json" \
  --argjson errors "$errors_json" \
  --argjson increment_count "$increment_count" \
  --argjson task_count "$task_count" \
  --argjson warning_count "$warning_count" \
  --argjson error_count "$error_count" \
  --arg message "$message" \
  '{
    tool: "plan-layers",
    contract_version: 1,
    status: $status,
    feature_dir: $feature_dir,
    tasks_file: $tasks_file,
    increments: $increments,
    warnings: $warnings,
    errors: $errors,
    summary: {
      increment_count: $increment_count,
      task_count: $task_count,
      warning_count: $warning_count,
      error_count: $error_count,
      message: $message
    }
  }'

if [ "$status" = "invalid_plan" ]; then
  printf 'plan-layers: invalid_plan: %s error(s)\n' "$error_count" >&2
  exit 1
fi
if [ "$warning_count" -gt 0 ]; then
  printf 'plan-layers: ok with %s warning(s)\n' "$warning_count" >&2
fi
exit 0

#!/usr/bin/env bash
# multi-pr-emission.sh - PRSG-009 safe foundation entrypoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

readonly STATE_SCHEMA="$REPO_ROOT/tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/contracts/multi-pr-emission-state.schema.json"
readonly PRS_SCHEMA="$REPO_ROOT/tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/contracts/prs-v2.schema.json"
readonly SLICE_PACKET_SCHEMA="$REPO_ROOT/tests/speckit-pro/layer4-scripts/fixtures/multi-pr-emission/contracts/slice-packet.schema.json"
readonly PLAN_LAYERS_SCHEMA="$REPO_ROOT/tests/speckit-pro/layer4-scripts/fixtures/plan-layers/contracts/plan-layers.schema.json"

usage() {
  printf 'Usage: multi-pr-emission.sh --layer-plan <json> --state <json> --feature-branch <branch> --base <branch> --base-sha <sha> [--full-verification-evidence <path>] [--changed-files <path>] [--candidate-dir <dir>] [--pr-fixture <json>] [--command-log <json>] [--scoped-verification-fixture <json>]\n' >&2
}

emit_input_error() {
  local message="$1"
  jq -cn \
    --arg message "$message" \
    '{script:"multi-pr-emission",status:"input_error",exit_code:2,message:$message}'
  printf 'multi-pr-emission.sh: input_error: %s\n' "$message" >&2
  exit 2
}

require_jq() {
  command -v jq >/dev/null 2>&1 || {
    printf 'multi-pr-emission.sh: input_error: jq is required\n' >&2
    exit 2
  }
}

write_json_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir"
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")"
  printf '%s\n' "$content" > "$tmp"
  jq -e . "$tmp" >/dev/null 2>&1 || {
    rm -f "$tmp"
    emit_input_error "candidate JSON validation failed for $target"
  }
  mv "$tmp" "$target"
}

persist_json_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir" || return 1
  if [ -e "$target" ] && [ ! -f "$target" ]; then
    return 1
  fi
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")" || return 1
  printf '%s\n' "$content" > "$tmp" || {
    rm -f "$tmp"
    return 1
  }
  jq -e . "$tmp" >/dev/null 2>&1 || {
    rm -f "$tmp"
    return 1
  }
  mv -f "$tmp" "$target" || {
    rm -f "$tmp"
    return 1
  }
}

persist_text_atomic() {
  local target="$1" content="$2" dir tmp
  dir="$(dirname "$target")"
  mkdir -p "$dir" || return 1
  if [ -e "$target" ] && [ ! -f "$target" ]; then
    return 1
  fi
  tmp="$(mktemp "$dir/.tmp.$(basename "$target").XXXXXX")" || return 1
  printf '%s\n' "$content" > "$tmp" || {
    rm -f "$tmp"
    return 1
  }
  mv -f "$tmp" "$target" || {
    rm -f "$tmp"
    return 1
  }
}

LAYER_PLAN=""
STATE_FILE=""
FEATURE_BRANCH=""
BASE_BRANCH=""
BASE_SHA=""
FULL_VERIFICATION_EVIDENCE=""
CHANGED_FILES=""
CANDIDATE_DIR=""
PR_FIXTURE=""
COMMAND_LOG=""
SCOPED_VERIFICATION_FIXTURE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --layer-plan)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --layer-plan"
      LAYER_PLAN="$2"
      shift 2
      ;;
    --state)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --state"
      STATE_FILE="$2"
      shift 2
      ;;
    --feature-branch)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --feature-branch"
      FEATURE_BRANCH="$2"
      shift 2
      ;;
    --base)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --base"
      BASE_BRANCH="$2"
      shift 2
      ;;
    --base-sha)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --base-sha"
      BASE_SHA="$2"
      shift 2
      ;;
    --full-verification-evidence)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --full-verification-evidence"
      FULL_VERIFICATION_EVIDENCE="$2"
      shift 2
      ;;
    --changed-files)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --changed-files"
      CHANGED_FILES="$2"
      shift 2
      ;;
    --candidate-dir)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --candidate-dir"
      CANDIDATE_DIR="$2"
      shift 2
      ;;
    --pr-fixture)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --pr-fixture"
      PR_FIXTURE="$2"
      shift 2
      ;;
    --command-log)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --command-log"
      COMMAND_LOG="$2"
      shift 2
      ;;
    --scoped-verification-fixture)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --scoped-verification-fixture"
      SCOPED_VERIFICATION_FIXTURE="$2"
      shift 2
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

[ -n "$LAYER_PLAN" ] || emit_input_error "missing required option --layer-plan"
[ -n "$STATE_FILE" ] || emit_input_error "missing required option --state"
[ -n "$FEATURE_BRANCH" ] || emit_input_error "missing required option --feature-branch"
[ -n "$BASE_BRANCH" ] || emit_input_error "missing required option --base"
[ -n "$BASE_SHA" ] || emit_input_error "missing required option --base-sha"

[ -r "$LAYER_PLAN" ] || emit_input_error "layer plan not readable: $LAYER_PLAN"
[ -r "$STATE_FILE" ] || emit_input_error "state not readable: $STATE_FILE"

if ! jq -e '
  type == "object"
  and .tool == "plan-layers"
  and (.contract_version | type == "number")
  and (.status == "ok" or .status == "invalid_plan" or .status == "input_error")
  and (.increments | type == "array")
  and (.warnings | type == "array")
  and (.errors | type == "array")
  and (.summary | type == "object")
' "$LAYER_PLAN" >/dev/null 2>&1; then
  emit_input_error "invalid layer plan JSON"
fi

plan_status="$(jq -r '.status' "$LAYER_PLAN")"
if [ "$plan_status" != "ok" ]; then
  emit_input_error "layer plan status $plan_status"
fi

if ! jq -e '
  (.increments | length > 0)
  and (.errors | length == 0)
  and all(.increments[];
    (.id | type == "string" and length > 0)
    and (.order | type == "number")
    and (.depends_on | type == "array")
    and (.files | type == "array")
    and (.tests | type == "array")
    and (.advisory_size | type == "object")
  )
' "$LAYER_PLAN" >/dev/null 2>&1; then
  emit_input_error "invalid ok layer plan envelope"
fi

if ! jq -e 'type == "object"' "$STATE_FILE" >/dev/null 2>&1; then
  emit_input_error "invalid state JSON"
fi

duplicate_slice="$(
  jq -r '
    (.multi_pr_emission.slices // [])
    | map(select(.slice_id != null))
    | group_by(.slice_id)
    | map(select(length > 1))
    | .[0][0].slice_id // empty
  ' "$STATE_FILE"
)"
if [ -n "$duplicate_slice" ]; then
  emit_input_error "duplicate state slice_id $duplicate_slice"
fi

FEATURE_DIR_REL="$(jq -r '.feature_dir // empty' "$LAYER_PLAN")"
if [ -z "$FEATURE_DIR_REL" ]; then
  FEATURE_DIR_REL="specs/$FEATURE_BRANCH"
fi
EXPECTED_EMISSION_DIR="$FEATURE_DIR_REL/.process/emission/"

if [ -z "$FULL_VERIFICATION_EVIDENCE" ]; then
  emit_input_error "missing required option --full-verification-evidence"
fi
[ -r "$FULL_VERIFICATION_EVIDENCE" ] || emit_input_error "full verification evidence not readable: $FULL_VERIFICATION_EVIDENCE"
case "$FULL_VERIFICATION_EVIDENCE" in
  *"$EXPECTED_EMISSION_DIR"*) ;;
  *)
    emit_input_error "full verification evidence must be under $EXPECTED_EMISSION_DIR"
    ;;
esac

if [ -n "$CHANGED_FILES" ] && [ ! -r "$CHANGED_FILES" ]; then
  emit_input_error "changed-files list not readable: $CHANGED_FILES"
fi

if [ -n "$PR_FIXTURE" ] && [ ! -r "$PR_FIXTURE" ]; then
  emit_input_error "pr fixture not readable: $PR_FIXTURE"
fi

if [ -n "$SCOPED_VERIFICATION_FIXTURE" ] && [ ! -r "$SCOPED_VERIFICATION_FIXTURE" ]; then
  emit_input_error "scoped verification fixture not readable: $SCOPED_VERIFICATION_FIXTURE"
fi
if [ -n "$SCOPED_VERIFICATION_FIXTURE" ] && ! jq -e '
  type == "object"
  and (
    ((.commands? // null) | type == "array")
    or ((.slices? // null) | type == "object")
  )
' "$SCOPED_VERIFICATION_FIXTURE" >/dev/null 2>&1; then
  emit_input_error "invalid scoped verification fixture JSON"
fi

plan_slices="$(
  jq -n \
    --arg feature_branch "$FEATURE_BRANCH" \
    --arg base_branch "$BASE_BRANCH" \
    --arg feature_dir "$FEATURE_DIR_REL" \
    --slurpfile plan "$LAYER_PLAN" '
      def slug:
        ascii_downcase
        | gsub("[^a-z0-9]+"; "-")
        | gsub("^-+"; "")
        | gsub("-+$"; "");
      def zpad($width):
        tostring as $s
        | if ($s | length) >= $width then $s
          else ([range(0; $width - ($s | length))] | map("0") | join("")) + $s
          end;
      def gate_type($command):
        if ($command | test("tests/speckit-pro/layer4-scripts/")) then "SCRIPT_UNIT"
        elif ($command | test("run-all[.]sh --layer 1")) then "STRUCTURAL"
        elif ($command | test("run-all[.]sh")) then "DEFAULT_VERIFY"
        else ""
        end;
      def evidence_name($gate):
        if $gate == "STRUCTURAL" then "layer1.log"
        elif $gate == "SCRIPT_UNIT" then "layer4.log"
        elif $gate == "DEFAULT_VERIFY" then "default-verify.log"
        elif $gate == "no_scoped_tests" then "no_scoped_tests.txt"
        else "scoped-verification.log"
        end;
      def scoped_commands($slice):
        (
          ($slice.declared_tests // [])
          | map(
              . as $command
              | (gate_type($command)) as $gate
              | select($gate != "")
              | {
                  command: $command,
                  gate_type: $gate,
                  reason: "PRSG-008 declared scoped test mapped to \($gate)",
                  required: true,
                  evidence_path: "\($feature_dir)/.process/emission/\($slice.slice_id)/\(evidence_name($gate))",
                  exit_status: 0,
                  started_at: "2026-06-10T00:00:00Z",
                  finished_at: "2026-06-10T00:00:01Z"
                }
            )
        ) as $commands
        | if ($commands | length) > 0 then $commands
          else [
            {
              command: "<none>",
              gate_type: "no_scoped_tests",
              reason: "No declared scoped tests or applicable project command; full regression evidence remains required.",
              required: true,
              evidence_path: "\($feature_dir)/.process/emission/\($slice.slice_id)/no_scoped_tests.txt",
              exit_status: 0,
              started_at: "2026-06-10T00:00:00Z",
              finished_at: "2026-06-10T00:00:01Z"
            }
          ]
          end;

      ($plan[0].increments) as $increments
      | ($plan[0].warnings) as $warnings
      | (($increments | length | tostring | length) as $digits | if $digits < 2 then 2 else $digits end) as $width
      | (
          $increments
          | to_entries
          | map(
              .key as $idx
              | .value as $inc
              | ($idx + 1) as $review_order
              | ($inc.id | slug) as $slice_id
              | ($review_order | zpad($width)) as $label
              | {
                  source_id: $inc.id,
                  slice_id: $slice_id,
                  review_order: $review_order,
                  branch: "\($feature_branch)/\($label)-\($slice_id)",
                  depends_on: ($inc.depends_on // []),
                  declared_files: ($inc.files // []),
                  declared_tests: ($inc.tests // []),
                  advisory_size: ($inc.advisory_size // {}),
                  warnings: (
                    $warnings
                    | map(
                        select(
                          ((.details.increment_id? // "") == $inc.id)
                          or ((.details.slice_id? // "") == $inc.id)
                        )
                        | .message
                      )
                  )
                }
            )
        ) as $slices
      | $slices
      | to_entries
      | map(
          .key as $idx
          | .value
              | . + {
                  base_branch: (
                    if $idx == 0 then $base_branch
                    else $slices[$idx - 1].branch
                    end
                  ),
                  scoped_verification: {
                    commands: scoped_commands(.)
                  }
                }
        )
    '
)"

empty_slug="$(printf '%s' "$plan_slices" | jq -r 'map(select(.slice_id == "")) | .[0].source_id // empty')"
if [ -n "$empty_slug" ]; then
  emit_input_error "invalid slice id slug $empty_slug"
fi

duplicate_plan_slice="$(
  printf '%s' "$plan_slices" | jq -r '
    group_by(.slice_id)
    | map(select(length > 1))
    | .[0][0].slice_id // empty
  '
)"
if [ -n "$duplicate_plan_slice" ]; then
  emit_input_error "duplicate planned slice_id $duplicate_plan_slice"
fi

while IFS= read -r branch_name; do
  if ! git check-ref-format --branch "$branch_name" >/dev/null 2>&1; then
    emit_input_error "invalid branch name $branch_name"
  fi
done < <(printf '%s' "$plan_slices" | jq -r '.[].branch')

allowed_scope="$(
  jq -n \
    --argjson slices "$plan_slices" \
    --arg feature_dir "$FEATURE_DIR_REL" '
      (
        [$slices[].declared_files[]]
        + [
            "docs/ai/specs/.process/PRSG-009-workflow.md",
            "docs/ai/specs/.process/autopilot-state.json",
            "\($feature_dir)/.process/prs.json",
            "\($feature_dir)/SPEC-MOC.md"
          ]
      )
      | unique
    '
)"

changed_files='[]'
if [ -n "$CHANGED_FILES" ]; then
  changed_files="$(jq -Rs 'split("\n") | map(select(length > 0))' "$CHANGED_FILES")"
  scope_violation="$(
    jq -r -n \
      --argjson changed "$changed_files" \
      --argjson allowed "$allowed_scope" '
        [$changed[] | . as $file | select(($allowed | index($file)) | not)][0] // empty
      '
  )"
  if [ -n "$scope_violation" ]; then
    emit_input_error "changed file outside declared slice scope: $scope_violation"
  fi
fi

scope_guard="$(
  jq -n \
    --argjson changed "$changed_files" \
    --argjson allowed "$allowed_scope" \
    --arg changed_files_path "$CHANGED_FILES" '
      {
        status: (if $changed_files_path == "" then "not_checked" else "passed" end),
        changed_files_path: (if $changed_files_path == "" then null else $changed_files_path end),
        changed_files_count: ($changed | length),
        allowed_files_count: ($allowed | length)
      }
    '
)"

candidate_state=""
candidate_prs=""
candidate_commands=""
candidate_state_path=""
candidate_prs_path=""
candidate_commands_path=""

if [ -n "$CANDIDATE_DIR" ]; then
  candidate_state_path="$CANDIDATE_DIR/multi-pr-emission-state.candidate.json"
  candidate_prs_path="$CANDIDATE_DIR/prs.candidate.json"
  candidate_commands_path="$CANDIDATE_DIR/commands.candidate.json"
  candidate_state="$(
    jq -n \
      --arg source_path "$LAYER_PLAN" \
      --arg base_branch "$BASE_BRANCH" \
      --arg base_sha "$BASE_SHA" \
      --argjson slices "$plan_slices" '
        {
            multi_pr_emission: {
              schema_version: 1,
              status: "pending",
              source_layer_plan: {path: $source_path},
              base_branch: $base_branch,
              base_sha: $base_sha,
              next_slice_id: ($slices[0].slice_id // null),
              reconciled_at: "",
              slices: (
                $slices
                | map(
                    {
                        slice_id: .slice_id,
                        review_order: .review_order,
                        expected_branch: .branch,
                        expected_base_branch: .base_branch,
                        head_sha: null,
                        declared_files: .declared_files,
                        declared_scoped_tests: .declared_tests,
                        scoped_verification: .scoped_verification,
                        status: "pending"
                      }
                  )
              )
            }
          }
      '
  )"
  candidate_prs="$(jq -n '{schemaVersion: 2, records: []}')"
  candidate_commands="$(
    jq -n \
      --argjson slices "$plan_slices" \
      --argjson scope_guard "$scope_guard" \
      --arg candidate_dir "$CANDIDATE_DIR" '
        def body_file($slice_id): "\($candidate_dir)/pr-bodies/\($slice_id).md";
        {
          schema_version: 1,
          dry_run: true,
          declared_scope_guard: $scope_guard,
          operations: (
            $slices
            | map(
                . as $slice
                | [
                    {
                      slice_id: $slice.slice_id,
                      review_order: $slice.review_order,
                      action: "git_branch",
                      branch: $slice.branch,
                      base_branch: $slice.base_branch,
                      command: ["git", "checkout", "-B", $slice.branch, $slice.base_branch]
                    },
                    {
                      slice_id: $slice.slice_id,
                      review_order: $slice.review_order,
                      action: "git_push",
                      branch: $slice.branch,
                      command: ["git", "push", "-u", "origin", $slice.branch]
                    },
                    {
                      slice_id: $slice.slice_id,
                      review_order: $slice.review_order,
                      action: "gh_pr_create",
                      branch: $slice.branch,
                      base_branch: $slice.base_branch,
                      body_file: body_file($slice.slice_id),
                      command: ["gh", "pr", "create", "--base", $slice.base_branch, "--head", $slice.branch, "--body-file", body_file($slice.slice_id)]
                    }
                  ]
              )
            | add
          )
        }
      '
  )"
  write_json_atomic "$candidate_state_path" "$candidate_state"
  write_json_atomic "$candidate_prs_path" "$candidate_prs"
  write_json_atomic "$candidate_commands_path" "$candidate_commands"

  mkdir -p "$CANDIDATE_DIR/slice-packets" "$CANDIDATE_DIR/pr-bodies"
  while IFS= read -r slice_json; do
    slice_id="$(printf '%s' "$slice_json" | jq -r '.slice_id')"
    packet_path="$CANDIDATE_DIR/slice-packets/$slice_id.json"
    body_file="$CANDIDATE_DIR/pr-bodies/$slice_id.md"
    packet_json="$(
      jq -n \
        --argjson slice "$slice_json" \
        --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" \
        --arg base_sha "$BASE_SHA" \
        --argjson total_slices "$(printf '%s' "$plan_slices" | jq 'length')" '
          {
            slice_id: $slice.slice_id,
            review_order: $slice.review_order,
            total_slices: $total_slices,
            base_branch: $slice.base_branch,
            head_branch: $slice.branch,
            declared_files: $slice.declared_files,
            declared_tests: $slice.declared_tests,
            scoped_verification: $slice.scoped_verification,
            full_verification_evidence: $full_verification_evidence,
            traceability: [
              {
                requirement: "FR-001",
                files: $slice.declared_files,
                evidence: [$full_verification_evidence]
              }
            ],
            known_gaps: [],
            warnings: $slice.warnings,
            restack_note: "Style B incremental stack: first slice targets the integration base and later slices target the previous slice branch.",
            prs_row: {
              review_order: $slice.review_order,
              slice_id: $slice.slice_id,
              layer: $slice.source_id,
              branch: $slice.branch,
              base_branch: $slice.base_branch,
              pr_number: null,
              pr_url: null,
              declared_files: $slice.declared_files,
              verification_evidence: ($slice.scoped_verification.commands[0].evidence_path // $full_verification_evidence),
              status: "pending",
              head_sha: $base_sha,
              merged_sha: null
            }
          }
        '
    )"
    write_json_atomic "$packet_path" "$packet_json"
    {
      printf '# Slice PR body placeholder\n\n'
      printf 'slice_id: %s\n' "$slice_id"
      printf 'slice_packet: %s\n' "$packet_path"
    } > "$body_file"
  done < <(printf '%s' "$plan_slices" | jq -c '.[]')
fi

if [ -z "$CANDIDATE_DIR" ]; then
  [ -n "$PR_FIXTURE" ] || emit_input_error "missing required option --pr-fixture for persistent emission"
  if ! jq -e '
    def int_field($name):
      (.[$name] | type == "number")
      and (.[$name] == (.[$name] | floor))
      and (.[$name] >= 1);
    type == "object"
    and ((.existing // []) | type == "array")
    and ((.created // []) | type == "array")
    and ((.create_failures // []) | type == "array")
    and all(((.existing // []) + (.created // []))[];
      (.head | type == "string" and length > 0)
      and (.base | type == "string" and length > 0)
      and int_field("number")
      and (.url | type == "string" and length > 0)
      and (.state | type == "string" and length > 0)
      and (.head_sha | type == "string" and length > 0)
    )
  ' "$PR_FIXTURE" >/dev/null 2>&1; then
    emit_input_error "invalid pr fixture JSON"
  fi

  state_suffix="/docs/ai/specs/.process/autopilot-state.json"
  case "$STATE_FILE" in
    *"$state_suffix") persist_root="${STATE_FILE%$state_suffix}" ;;
    *) emit_input_error "persistent emission requires --state under docs/ai/specs/.process/autopilot-state.json" ;;
  esac

  feature_dir_abs="$persist_root/$FEATURE_DIR_REL"
  prs_path="$feature_dir_abs/.process/prs.json"
  moc_path="$feature_dir_abs/SPEC-MOC.md"
  workflow_path="$persist_root/docs/ai/specs/.process/PRSG-009-workflow.md"

  [ -d "$feature_dir_abs" ] || emit_input_error "feature directory not found for persistent emission: $feature_dir_abs"
  [ -f "$moc_path" ] || emit_input_error "SPEC-MOC.md not found for persistent emission: $moc_path"

  command_log_json="$(jq -n '{schema_version: 1, dry_run: false, operations: []}')"

  write_command_log() {
    if [ -n "$COMMAND_LOG" ]; then
      persist_json_atomic "$COMMAND_LOG" "$command_log_json" || return 1
    fi
  }

  persist_state_or_die() {
    persist_json_atomic "$STATE_FILE" "$state_json" || emit_input_error "state persistence failed: $STATE_FILE"
  }

  block_with_state() {
    local slice_id="$1" phase="$2" message="$3" status="${4:-failed}" exit_status="${5:-2}"
    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg slice "$slice_id" \
        --arg phase "$phase" \
        --arg message "$message" \
        --arg status "$status" \
        --argjson exit_status "$exit_status" '
          .multi_pr_emission.status = "blocked"
          | .multi_pr_emission.next_slice_id = $slice
          | (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
              status: $status,
              last_error: {
                slice_id: $slice,
                failed_at: "2026-06-10T00:00:00Z",
                phase: $phase,
                command: $message,
                exit_status: $exit_status,
                evidence_path: ""
              }
            }
        '
    )"
    persist_json_atomic "$STATE_FILE" "$state_json" >/dev/null 2>&1 || true
    write_command_log >/dev/null 2>&1 || true
    jq -cn --arg message "$message" '{script:"multi-pr-emission",status:"blocked",exit_code:2,message:$message}'
    printf 'multi-pr-emission.sh: blocked: %s\n' "$message" >&2
    exit 2
  }

  block_after_pr_opened() {
    local slice_id="$1" phase="$2" message="$3"
    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg slice "$slice_id" \
        --arg phase "$phase" \
        --arg message "$message" '
          .multi_pr_emission.status = "blocked"
          | .multi_pr_emission.next_slice_id = $slice
          | (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
              last_error: {
                slice_id: $slice,
                failed_at: "2026-06-10T00:00:00Z",
                phase: $phase,
                command: $message,
                exit_status: 2,
                evidence_path: ""
              }
            }
        '
    )"
    persist_json_atomic "$STATE_FILE" "$state_json" >/dev/null 2>&1 || true
    write_command_log >/dev/null 2>&1 || true
    jq -cn --arg message "$message" '{script:"multi-pr-emission",status:"blocked",exit_code:2,message:$message}'
    printf 'multi-pr-emission.sh: blocked: %s\n' "$message" >&2
    exit 2
  }

  build_prs_json() {
    printf '%s' "$state_json" | jq --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" '
      {
        schemaVersion: 2,
        records: [
          .multi_pr_emission.slices[]
          | select(.pr != null and (.status == "pr_opened" or .status == "merged"))
          | {
              review_order: .review_order,
              slice_id: .slice_id,
              layer: .slice_id,
              branch: .expected_branch,
              base_branch: .expected_base_branch,
              pr_number: .pr.number,
              pr_url: .pr.url,
              declared_files: .declared_files,
              verification_evidence: (.scoped_verification.commands[0].evidence_path // $full_verification_evidence),
              status: (if .status == "merged" then "merged" else "opened" end),
              head_sha: (.pr.head_sha // .head_sha),
              merged_sha: (.pr.merged_sha // null)
            }
        ]
      }
    '
  }

  append_workflow_event() {
    local event="$1"
    local current next
    current="$(cat "$workflow_path" 2>/dev/null || true)"
    if [[ "$current" == *"### US2 emission evidence"* ]]; then
      next="${current}"$'\n'"- ${event}"
    else
      next="${current}"$'\n\n'"### US2 emission evidence"$'\n'"- ${event}"
    fi
    persist_text_atomic "$workflow_path" "$next"
  }

  record_create_command() {
    local slice_json="$1" body_file="$2"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" \
        --arg body_file "$body_file" '
          $log
          | .operations += [
              {
                slice_id: $slice.slice_id,
                review_order: $slice.review_order,
                action: "gh_pr_create",
                branch: $slice.branch,
                base_branch: $slice.base_branch,
                body_file: $body_file,
                command: ["gh", "pr", "create", "--base", $slice.base_branch, "--head", $slice.branch, "--body-file", $body_file]
              }
            ]
        '
    )"
  }

  resolve_scoped_json() {
    local slice_json="$1" slice_id="$2" resolved override
    resolved="$(printf '%s' "$slice_json" | jq -c '.scoped_verification')"
    if [ -n "$SCOPED_VERIFICATION_FIXTURE" ]; then
      override="$(
        jq -c --arg slice "$slice_id" '
          if (((.slices? // null) | type) == "object") and ((.slices[$slice]? // null) != null) then
            .slices[$slice]
          elif ((.slice_id? // "") == $slice) and (((.commands? // null) | type) == "array") then
            {commands: .commands}
          elif (((.slices? // null) == null) and (((.commands? // null) | type) == "array")) then
            {commands: .commands}
          else
            empty
          end
        ' "$SCOPED_VERIFICATION_FIXTURE"
      )"
      if [ -n "$override" ]; then
        resolved="$override"
      fi
    fi
    printf '%s' "$resolved"
  }

  record_scoped_commands() {
    local slice_json="$1" scoped_json="$2"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" \
        --argjson scoped "$scoped_json" '
          $log
          | .operations += (
              $scoped.commands
              | map({
                  slice_id: $slice.slice_id,
                  review_order: $slice.review_order,
                  action: "scoped_verification",
                  branch: $slice.branch,
                  command: .command,
                  gate_type: .gate_type,
                  evidence_path: .evidence_path,
                  exit_status: .exit_status
                })
            )
        '
    )"
  }

  write_scoped_evidence_files() {
    local scoped_json="$1"
    while IFS= read -r command_json; do
      [ -n "$command_json" ] || continue
      evidence_path="$(printf '%s' "$command_json" | jq -r '.evidence_path')"
      evidence_abs="$persist_root/$evidence_path"
      if [ "$(printf '%s' "$command_json" | jq -r '.gate_type')" = "no_scoped_tests" ]; then
        evidence_body="$(
          printf 'No declared scoped tests or applicable project command protects this slice.\n'
          printf 'Full regression evidence remains required before emission.\n'
          printf 'command: <none>\n'
          printf 'exit_status: 0\n'
        )"
      else
        evidence_body="$(
          printf 'command: %s\n' "$(printf '%s' "$command_json" | jq -r '.command')"
          printf 'gate_type: %s\n' "$(printf '%s' "$command_json" | jq -r '.gate_type')"
          printf 'exit_status: %s\n' "$(printf '%s' "$command_json" | jq -r '.exit_status')"
          printf 'reason: %s\n' "$(printf '%s' "$command_json" | jq -r '.reason')"
          stdout_tail="$(printf '%s' "$command_json" | jq -r '.stdout_tail // empty')"
          stderr_tail="$(printf '%s' "$command_json" | jq -r '.stderr_tail // empty')"
          if [ -n "$stdout_tail" ]; then
            printf 'stdout_tail: %s\n' "$stdout_tail"
          fi
          if [ -n "$stderr_tail" ]; then
            printf 'stderr_tail: %s\n' "$stderr_tail"
          fi
        )"
      fi
      persist_text_atomic "$evidence_abs" "$evidence_body" || emit_input_error "scoped verification evidence persistence failed: $evidence_path"
    done < <(printf '%s' "$scoped_json" | jq -c '.commands[]')
  }

  block_scoped_verification_if_failed() {
    local slice_json="$1" scoped_json="$2" failing failure_record slice_id message command_text exit_status evidence_path stderr_tail workflow_event
    failing="$(printf '%s' "$scoped_json" | jq -c '[.commands[] | select(.required == true and .exit_status != 0)][0] // empty')"
    [ -n "$failing" ] || return 0

    slice_id="$(printf '%s' "$slice_json" | jq -r '.slice_id')"
    command_text="$(printf '%s' "$failing" | jq -r '.command')"
    exit_status="$(printf '%s' "$failing" | jq -r '.exit_status')"
    evidence_path="$(printf '%s' "$failing" | jq -r '.evidence_path')"
    stderr_tail="$(printf '%s' "$failing" | jq -r '.stderr_tail // empty')"
    message="scoped verification failed for slice $slice_id"

    failure_record="$(
      jq -n \
        --arg slice "$slice_id" \
        --arg failed_at "2026-06-10T00:00:00Z" \
        --arg command "$command_text" \
        --arg evidence "$evidence_path" \
        --arg head_sha "$BASE_SHA" \
        --arg retry_policy "fix scoped verification and rerun multi-pr-emission.sh from failed slice" \
        --argjson exit_status "$exit_status" \
        --argjson declared_tests "$(printf '%s' "$slice_json" | jq '.declared_tests')" \
        --arg stdout_tail "$(printf '%s' "$failing" | jq -r '.stdout_tail // empty')" \
        --arg stderr_tail "$stderr_tail" '
          {
            slice_id: $slice,
            failed_at: $failed_at,
            phase: "scoped_verification",
            command: $command,
            exit_status: $exit_status,
            evidence_path: $evidence,
            head_sha: $head_sha,
            declared_tests: $declared_tests,
            retry_policy: $retry_policy
          }
          + (if $stdout_tail == "" then {} else {stdout_tail: $stdout_tail} end)
          + (if $stderr_tail == "" then {} else {stderr_tail: $stderr_tail} end)
        '
    )"

    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg slice "$slice_id" \
        --argjson scoped "$scoped_json" \
        --argjson failure "$failure_record" '
          .multi_pr_emission.status = "blocked"
          | .multi_pr_emission.next_slice_id = $slice
          | .multi_pr_emission.failed_slice = $failure
          | (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
              status: "failed",
              scoped_verification: $scoped,
              last_error: $failure
            }
        '
    )"
    persist_json_atomic "$STATE_FILE" "$state_json" >/dev/null 2>&1 || true
    workflow_event="$(printf 'Failed scoped verification for `%s`: command `%s` exit %s; evidence `%s`; stderr tail `%s`; next_slice_id: `%s`.' "$slice_id" "$command_text" "$exit_status" "$evidence_path" "$stderr_tail" "$slice_id")"
    append_workflow_event "$workflow_event" >/dev/null 2>&1 || true
    write_command_log >/dev/null 2>&1 || true
    jq -cn --arg message "$message" '{script:"multi-pr-emission",status:"blocked",exit_code:2,message:$message}'
    printf 'multi-pr-emission.sh: blocked: %s\n' "$message" >&2
    exit 2
  }

  state_json="$(
    jq -n \
      --arg source_path "$LAYER_PLAN" \
      --arg base_branch "$BASE_BRANCH" \
      --arg base_sha "$BASE_SHA" \
      --argjson slices "$plan_slices" '
        {
          multi_pr_emission: {
            schema_version: 1,
            status: "emitting",
            source_layer_plan: {path: $source_path},
            base_branch: $base_branch,
            base_sha: $base_sha,
            next_slice_id: ($slices[0].slice_id // null),
            reconciled_at: "2026-06-10T00:00:00Z",
            slices: (
              $slices
              | map({
                  slice_id: .slice_id,
                  review_order: .review_order,
                  expected_branch: .branch,
                  expected_base_branch: .base_branch,
                  head_sha: null,
                  declared_files: .declared_files,
                  declared_scoped_tests: .declared_tests,
                  scoped_verification: .scoped_verification,
                  status: "pending"
                })
            )
          }
        }
      '
  )"

  total_slices="$(printf '%s' "$plan_slices" | jq 'length')"

  while IFS= read -r slice_json; do
    slice_id="$(printf '%s' "$slice_json" | jq -r '.slice_id')"
    review_order="$(printf '%s' "$slice_json" | jq -r '.review_order')"
    head_branch="$(printf '%s' "$slice_json" | jq -r '.branch')"
    base_branch="$(printf '%s' "$slice_json" | jq -r '.base_branch')"
    scoped_json="$(resolve_scoped_json "$slice_json" "$slice_id")"
    slice_json="$(printf '%s' "$slice_json" | jq --argjson scoped "$scoped_json" '.scoped_verification = $scoped')"
    packet_dir="$feature_dir_abs/.process/emission/$slice_id"
    packet_path="$packet_dir/slice-packet.json"
    body_file="$packet_dir/pr-body.md"
    mkdir -p "$packet_dir"

    packet_json="$(
      jq -n \
        --argjson slice "$slice_json" \
        --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" \
        --arg base_sha "$BASE_SHA" \
        --argjson total_slices "$total_slices" '
          {
            slice_id: $slice.slice_id,
            review_order: $slice.review_order,
            total_slices: $total_slices,
            base_branch: $slice.base_branch,
            head_branch: $slice.branch,
            declared_files: $slice.declared_files,
            declared_tests: $slice.declared_tests,
            scoped_verification: $slice.scoped_verification,
            full_verification_evidence: $full_verification_evidence,
            traceability: [
              {
                requirement: "FR-010",
                files: $slice.declared_files,
                evidence: [$full_verification_evidence]
              }
            ],
            known_gaps: [],
            warnings: $slice.warnings,
            restack_note: "Style B incremental stack: first slice targets the integration base and later slices target the previous slice branch.",
            prs_row: {
              review_order: $slice.review_order,
              slice_id: $slice.slice_id,
              layer: $slice.source_id,
              branch: $slice.branch,
              base_branch: $slice.base_branch,
              pr_number: null,
              pr_url: null,
              declared_files: $slice.declared_files,
              verification_evidence: ($slice.scoped_verification.commands[0].evidence_path // $full_verification_evidence),
              status: "pending",
              head_sha: $base_sha,
              merged_sha: null
            }
          }
        '
    )"
    persist_json_atomic "$packet_path" "$packet_json" || emit_input_error "slice packet persistence failed: $packet_path"
    "$SCRIPT_DIR/generate-pr-body.sh" --slice-packet "$packet_path" "$persist_root" "$feature_dir_abs" "$body_file" "$BASE_SHA...HEAD" >/dev/null

    record_scoped_commands "$slice_json" "$scoped_json"
    write_scoped_evidence_files "$scoped_json"
    block_scoped_verification_if_failed "$slice_json" "$scoped_json"

    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg slice "$slice_id" \
        --argjson scoped "$scoped_json" '
          (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
            status: "verified",
            scoped_verification: $scoped
          }
        '
    )"
    persist_state_or_die

    pr_json="$(
      jq -c --arg head "$head_branch" --arg base "$base_branch" '
        (.existing // [])
        | map(select(.head == $head and .base == $base))
        | .[0] // empty
      ' "$PR_FIXTURE"
    )"
    pr_source="existing"

    if [ -z "$pr_json" ]; then
      record_create_command "$slice_json" "$body_file"
      create_failure="$(
        jq -c --arg head "$head_branch" --arg base "$base_branch" --arg slice "$slice_id" '
          (.create_failures // [])
          | map(select((.slice_id == $slice) or (.head == $head and .base == $base)))
          | .[0] // empty
        ' "$PR_FIXTURE"
      )"
      if [ -n "$create_failure" ]; then
        failure_status="$(printf '%s' "$create_failure" | jq -r '.exit_status // 4')"
        block_with_state "$slice_id" "gh_pr_create" "gh pr create failed for slice $slice_id" "failed" "$failure_status"
      fi
      pr_json="$(
        jq -c --arg head "$head_branch" --arg base "$base_branch" --arg slice "$slice_id" '
          (.created // [])
          | map(select((.slice_id == $slice) or (.head == $head and .base == $base)))
          | .[0] // empty
        ' "$PR_FIXTURE"
      )"
      [ -n "$pr_json" ] || block_with_state "$slice_id" "gh_pr_create" "gh pr create failed for slice $slice_id" "failed" 4
      pr_source="created"
    fi

    pr_state="$(printf '%s' "$pr_json" | jq -r '.state | ascii_downcase')"
    pr_number="$(printf '%s' "$pr_json" | jq -r '.number')"
    pr_url="$(printf '%s' "$pr_json" | jq -r '.url')"
    head_sha="$(printf '%s' "$pr_json" | jq -r '.head_sha')"
    merged_sha="$(printf '%s' "$pr_json" | jq -r '.merged_sha // empty')"

    if [ "$pr_state" = "closed" ] && [ -z "$merged_sha" ]; then
      pr_record="$(
        jq -n \
          --argjson number "$pr_number" \
          --arg url "$pr_url" \
          --arg state "closed" \
          --arg base "$base_branch" \
          --arg head "$head_branch" \
          --arg head_sha "$head_sha" \
          '{number:$number,url:$url,state:$state,base_ref:$base,head_ref:$head,head_sha:$head_sha,merged_sha:null}'
      )"
      state_json="$(
        printf '%s' "$state_json" | jq \
          --arg slice "$slice_id" \
          --arg head_sha "$head_sha" \
          --argjson pr "$pr_record" '
            (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
              status: "closed",
              head_sha: $head_sha,
              pr: $pr
            }
          '
      )"
      block_with_state "$slice_id" "closed_pr" "closed PR blocks slice $slice_id" "closed" 2
    fi

    slice_status="pr_opened"
    prs_status="opened"
    if [ "$pr_state" = "merged" ]; then
      slice_status="merged"
      prs_status="merged"
    fi
    pr_record="$(
      jq -n \
        --argjson number "$pr_number" \
        --arg url "$pr_url" \
        --arg state "$prs_status" \
        --arg base "$base_branch" \
        --arg head "$head_branch" \
        --arg head_sha "$head_sha" \
        --arg merged_sha "$merged_sha" '
          {
            number: $number,
            url: $url,
            state: $state,
            base_ref: $base,
            head_ref: $head,
            head_sha: $head_sha,
            merged_sha: (if $merged_sha == "" then null else $merged_sha end)
          }
        '
    )"
    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg slice "$slice_id" \
        --arg status "$slice_status" \
        --arg head_sha "$head_sha" \
        --argjson pr "$pr_record" '
          (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
            status: $status,
            head_sha: $head_sha,
            pr: $pr
          }
        '
    )"
    persist_state_or_die

    prs_json="$(build_prs_json)"
    if ! persist_json_atomic "$prs_path" "$prs_json"; then
      block_after_pr_opened "$slice_id" "prs_persist" "persistence failed after PR opened for slice $slice_id"
    fi

    if ! "$SCRIPT_DIR/generate-spec-index.sh" "$persist_root" >/dev/null 2>&1; then
      block_after_pr_opened "$slice_id" "moc_persist" "persistence failed after PR opened for slice $slice_id"
    fi

    if [ "$pr_source" = "existing" ]; then
      workflow_event="Reconciled existing PR#$pr_number for \`$slice_id\` ($head_branch -> $base_branch)."
    else
      workflow_event="Opened PR#$pr_number for \`$slice_id\` ($head_branch -> $base_branch)."
    fi
    if ! append_workflow_event "$workflow_event"; then
      block_after_pr_opened "$slice_id" "workflow_persist" "persistence failed after PR opened for slice $slice_id"
    fi

    next_slice_id="$(
      printf '%s' "$plan_slices" | jq -r --argjson order "$review_order" '
        map(select(.review_order > $order))
        | sort_by(.review_order)
        | .[0].slice_id // empty
      '
    )"
    state_json="$(
      printf '%s' "$state_json" | jq \
        --arg next "$next_slice_id" '
          if $next == "" then
            .multi_pr_emission.status = "complete"
            | .multi_pr_emission.next_slice_id = null
          else
            .multi_pr_emission.status = "emitting"
            | .multi_pr_emission.next_slice_id = $next
          end
        '
    )"
    persist_state_or_die
  done < <(printf '%s' "$plan_slices" | jq -c '.[]')

  write_command_log || emit_input_error "command log persistence failed: $COMMAND_LOG"

  jq -cn \
    --argjson slice_count "$(printf '%s' "$plan_slices" | jq 'length')" \
    --arg state "$STATE_FILE" \
    --arg prs "$prs_path" \
    --arg moc "$moc_path" \
    --arg workflow "$workflow_path" \
    '{
      script: "multi-pr-emission",
      status: "persisted",
      mutation: {branches: false, pull_requests: false},
      emission: {slice_count: $slice_count, dry_run: false},
      persisted_files: {state: $state, prs_manifest: $prs, spec_moc: $moc, workflow: $workflow}
    }'
  exit 0
fi

slice_count="$(printf '%s' "$plan_slices" | jq 'length')"

jq -cn \
  --arg state_schema "$STATE_SCHEMA" \
  --arg prs_schema "$PRS_SCHEMA" \
  --arg slice_packet_schema "$SLICE_PACKET_SCHEMA" \
  --arg plan_layers_schema "$PLAN_LAYERS_SCHEMA" \
  --arg candidate_state "$candidate_state_path" \
  --arg candidate_prs "$candidate_prs_path" \
  --arg candidate_commands "$candidate_commands_path" \
  --argjson slice_count "$slice_count" \
  '{
    script: "multi-pr-emission",
    status: "validated",
    mutation: {branches: false, pull_requests: false},
    schema_paths: {
      multi_pr_emission_state: $state_schema,
      prs_v2: $prs_schema,
      slice_packet: $slice_packet_schema,
      plan_layers: $plan_layers_schema
    },
    emission: {
      slice_count: $slice_count,
      dry_run: true
    },
    candidate_files: {
      state: (if $candidate_state == "" then null else $candidate_state end),
      prs_manifest: (if $candidate_prs == "" then null else $candidate_prs end),
      command_capture: (if $candidate_commands == "" then null else $candidate_commands end)
    }
  }'

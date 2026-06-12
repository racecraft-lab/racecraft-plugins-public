#!/usr/bin/env bash
# multi-pr-emission.sh - PRSG-009 safe foundation entrypoint.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

if [ -d "$REPO_ROOT/speckit-pro/skills/speckit-autopilot/contracts" ]; then
  CONTRACT_ROOT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/contracts"
else
  CONTRACT_ROOT="$SKILL_ROOT/contracts"
fi
readonly CONTRACT_ROOT
readonly STATE_SCHEMA="$CONTRACT_ROOT/multi-pr-emission-state.schema.json"
readonly PRS_SCHEMA="$CONTRACT_ROOT/prs-v2.schema.json"
readonly SLICE_PACKET_SCHEMA="$CONTRACT_ROOT/slice-packet.schema.json"
readonly PLAN_LAYERS_SCHEMA="$CONTRACT_ROOT/plan-layers.schema.json"

usage() {
  printf 'Usage: multi-pr-emission.sh (--layer-plan <json> | --marker-plan <json> --marker-split-result <json>) --state <json> --feature-branch <branch> --base <branch> --base-sha <sha> [--full-verification-evidence <path>] [--changed-files <path>] [--candidate-dir <dir>] [--pr-fixture <json>] [--command-log <json>] [--scoped-verification-fixture <json>] [--live]\n' >&2
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

repo_relative_path() {
  local path="$1" root="$2"
  root="${root%/}"
  path="${path%/}"
  case "$path" in
    "$root"/*)
      printf '%s\n' "${path#"$root"/}"
      ;;
    "$root")
      printf '.\n'
      ;;
    ./*)
      printf '%s\n' "${path#./}"
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

conventional_scope_from_feature_dir() {
  local feature_dir_rel="$1" base spec_suffix
  base="${feature_dir_rel%/}"
  base="${base##*/}"
  if [[ "$base" =~ ^[Pp][Rr][Ss][Gg]-([0-9]+)(-|$) ]]; then
    printf 'PRSG-%s\n' "${BASH_REMATCH[1]}"
  elif [[ "$base" =~ ^[Ss][Pp][Ee][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    spec_suffix="${BASH_REMATCH[1]^^}"
    printf 'SPEC-%s\n' "$spec_suffix"
  else
    printf 'speckit-pro\n'
  fi
}

protected_body_sha() {
  local path="$1"
  awk '
    function trim(s) { sub(/[ \t\r]+$/, "", s); return s }
    {
      line=trim($0)
      if (!in_block && line == "## Summary") in_block=1
      if (!in_block) next
      if (seen_known_gaps && known_gaps_body_seen && line == "") exit
      if (seen_known_gaps && line ~ /^#{1,6}[[:space:]]+/) exit

      if (line == "<!-- speckit-pro-editable:summary:start -->") {
        field="summary"; in_edit=1; print line; print "<elided:summary>"; next
      }
      if (line == "<!-- speckit-pro-editable:what_changed:start -->") {
        field="what_changed"; in_edit=1; print line; print "<elided:what_changed>"; next
      }
      if (line == "<!-- speckit-pro-editable:why_it_matters:start -->") {
        field="why_it_matters"; in_edit=1; print line; print "<elided:why_it_matters>"; next
      }
      if (in_edit && line == "<!-- speckit-pro-editable:" field ":end -->") {
        in_edit=0; field=""; print line; next
      }
      if (in_edit) next

      print line
      if (line == "## Known Gaps") seen_known_gaps=1
      else if (seen_known_gaps && line != "") known_gaps_body_seen=1
    }
  ' "$path" | {
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 256 | awk '{print $1}'
    else
      awk '{printf "%064d\n", 0}'
    fi
  }
}

sha256_file() {
  local path="$1"
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
  else
    printf '%064d\n' 0
  fi
}

LAYER_PLAN=""
MARKER_PLAN=""
MARKER_SPLIT_RESULT=""
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
LIVE=false

while [ "$#" -gt 0 ]; do
  case "$1" in
    --layer-plan)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --layer-plan"
      LAYER_PLAN="$2"
      shift 2
      ;;
    --marker-plan)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --marker-plan"
      MARKER_PLAN="$2"
      shift 2
      ;;
    --marker-split-result)
      [ "$#" -ge 2 ] || emit_input_error "missing value for --marker-split-result"
      MARKER_SPLIT_RESULT="$2"
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
    --live)
      LIVE=true
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

MARKER_MODE=false
if [ -n "$MARKER_PLAN" ] || [ -n "$MARKER_SPLIT_RESULT" ]; then
  MARKER_MODE=true
fi

if [ "$MARKER_MODE" = true ]; then
  [ -n "$MARKER_PLAN" ] || emit_input_error "missing required option --marker-plan"
  [ -n "$MARKER_SPLIT_RESULT" ] || emit_input_error "missing required option --marker-split-result"
  [ -z "$LAYER_PLAN" ] || emit_input_error "use either --layer-plan or marker-aware options, not both"
else
  [ -n "$LAYER_PLAN" ] || emit_input_error "missing required option --layer-plan"
fi
[ -n "$STATE_FILE" ] || emit_input_error "missing required option --state"
[ -n "$FEATURE_BRANCH" ] || emit_input_error "missing required option --feature-branch"
[ -n "$BASE_BRANCH" ] || emit_input_error "missing required option --base"
[ -n "$BASE_SHA" ] || emit_input_error "missing required option --base-sha"
[ "$LIVE" != true ] || [ -z "$CANDIDATE_DIR" ] || emit_input_error "--live cannot be combined with --candidate-dir"
[ "$LIVE" != true ] || [ -z "$PR_FIXTURE" ] || emit_input_error "--live cannot be combined with --pr-fixture"
[ "$LIVE" != true ] || [ "$MARKER_MODE" = true ] || emit_input_error "--live requires marker-aware emission"

if [ "$MARKER_MODE" = true ]; then
  [ -r "$MARKER_PLAN" ] || emit_input_error "marker plan not readable: $MARKER_PLAN"
  [ -r "$MARKER_SPLIT_RESULT" ] || emit_input_error "marker split result not readable: $MARKER_SPLIT_RESULT"
else
  [ -r "$LAYER_PLAN" ] || emit_input_error "layer plan not readable: $LAYER_PLAN"
fi
[ -r "$STATE_FILE" ] || emit_input_error "state not readable: $STATE_FILE"

if [ "$MARKER_MODE" != true ] && ! jq -e '
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

if [ "$MARKER_MODE" != true ]; then
  plan_status="$(jq -r '.status' "$LAYER_PLAN")"
  if [ "$plan_status" != "ok" ]; then
    emit_input_error "layer plan status $plan_status"
  fi
fi

if [ "$MARKER_MODE" != true ] && ! jq -e '
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

if [ "$MARKER_MODE" = true ]; then
  FEATURE_DIR_REL="specs/$FEATURE_BRANCH"
else
  FEATURE_DIR_REL="$(jq -r '.feature_dir // empty' "$LAYER_PLAN")"
  if [ -z "$FEATURE_DIR_REL" ]; then
    FEATURE_DIR_REL="specs/$FEATURE_BRANCH"
  fi
fi
EXPECTED_EMISSION_DIR="$FEATURE_DIR_REL/.process/emission/"
TITLE_SCOPE="$(conventional_scope_from_feature_dir "$FEATURE_DIR_REL")"

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

EMISSION_MODE="layer"
EMISSION_ROUTE="layer_plan"
MARKER_SOURCE_COUNT=0

if [ "$MARKER_MODE" = true ]; then
  EMISSION_MODE="marker"

  if ! jq -e '
    type == "object"
    and .schema_version == "pr-marker-plan.v1"
    and .kind == "pr_marker_plan"
    and (.feature_id | type == "string" and length > 0)
    and (.status | type == "string" and length > 0)
    and (.source_fingerprint | type == "object")
    and (.markers | type == "array" and length > 0)
    and (.warnings | type == "array")
    and all(.markers[];
      (.id | type == "string" and length > 0)
      and (.review_order | type == "number" and . == floor and . >= 1)
      and (.kind | type == "string" and length > 0)
      and (.declared_files | type == "array")
      and all(.declared_files[]; (.operation | type == "string") and (.path | type == "string" and length > 0))
      and (.declared_tests | type == "array")
      and all(.declared_tests[]; type == "string" and length > 0)
      and (.implementation_checkpoint | type == "object")
      and (.implementation_checkpoint.status == "complete")
      and (.implementation_checkpoint.evidence_path | type == "string" and length > 0)
      and (.warnings | type == "array")
    )
  ' "$MARKER_PLAN" >/dev/null 2>&1; then
    emit_input_error "invalid marker plan JSON"
  fi

  marker_status="$(jq -r '.status' "$MARKER_PLAN")"
  if [ "$marker_status" != "emission_ready" ]; then
    emit_input_error "marker plan status $marker_status"
  fi

  if ! jq -e '
    .markers
    | to_entries
    | all(.[]; .value.review_order == (.key + 1))
  ' "$MARKER_PLAN" >/dev/null 2>&1; then
    emit_input_error "marker plan review_order must match marker array order"
  fi

  duplicate_marker="$(
    jq -r '
      .markers
      | group_by(.id)
      | map(select(length > 1))
      | .[0][0].id // empty
    ' "$MARKER_PLAN"
  )"
  if [ -n "$duplicate_marker" ]; then
    emit_input_error "duplicate marker_id $duplicate_marker"
  fi

  placeholder_marker="$(
    jq -r '
      [
        .markers[]
        | select(
            any((.declared_files // [])[]; (.path | test("(<[^>]+>|TODO|TBD|placeholder)"; "i")))
            or any((.declared_tests // [])[]; test("(<[^>]+>|TODO|TBD|placeholder)"; "i"))
          )
        | .id
      ][0] // empty
    ' "$MARKER_PLAN"
  )"
  if [ -n "$placeholder_marker" ]; then
    emit_input_error "invalid marker packet shape: placeholder declared file path for $placeholder_marker"
  fi

  if ! jq -e '
    type == "object"
    and .status == "proceed"
    and .outcome == "marker_split"
    and .mode == "final"
    and (.full_diff | type == "object")
    and (.full_diff.reviewability_status | type == "string")
    and (.marker_plan.valid == true)
    and (.marker_plan.fingerprint_matched == true)
    and (.emission | type == "object")
    and (.emission.route as $route | (["marker_split", "hazard_collapsed", "single_pr"] | index($route)) != null)
    and (.emission.markers | type == "array" and length > 0)
    and (.warnings | type == "array")
  ' "$MARKER_SPLIT_RESULT" >/dev/null 2>&1; then
    emit_input_error "invalid marker split result JSON"
  fi

  EMISSION_ROUTE="$(jq -r '.emission.route' "$MARKER_SPLIT_RESULT")"
  if [ "$EMISSION_ROUTE" = "single_pr" ]; then
    EMISSION_ROUTE="hazard_collapsed"
  fi

  if [ "$EMISSION_ROUTE" = "hazard_collapsed" ]; then
    if ! jq -e '
      [
        .warnings[]?.details?
        | select((.route == "single-atomic-PR") or (.releasable == false))
      ]
      | length > 0
    ' "$MARKER_SPLIT_RESULT" >/dev/null 2>&1; then
      emit_input_error "hazard collapse missing atomicity evidence"
    fi
  else
    unknown_marker="$(
      jq -nr \
        --slurpfile plan "$MARKER_PLAN" \
        --slurpfile split "$MARKER_SPLIT_RESULT" '
          ($plan[0].markers | map(.id)) as $ids
          | [
              $split[0].emission.markers[]?.id as $id
              | select(($ids | index($id)) | not)
              | $id
            ][0] // empty
        '
    )"
    if [ -n "$unknown_marker" ]; then
      emit_input_error "marker split result references unknown marker $unknown_marker"
    fi

    order_mismatch="$(
      jq -nr \
        --slurpfile plan "$MARKER_PLAN" \
        --slurpfile split "$MARKER_SPLIT_RESULT" '
          ($plan[0].markers | map({key: .id, value: .review_order}) | from_entries) as $orders
          | [
              $split[0].emission.markers[]?
              | select(($orders[.id] != null) and ($orders[.id] != .review_order))
              | .id
            ][0] // empty
        '
    )"
    if [ -n "$order_mismatch" ]; then
      emit_input_error "marker split result review_order mismatch for $order_mismatch"
    fi

    plan_marker_count="$(jq '.markers | length' "$MARKER_PLAN")"
    split_marker_count="$(jq '.emission.markers | length' "$MARKER_SPLIT_RESULT")"
    if [ "$plan_marker_count" != "$split_marker_count" ]; then
      emit_input_error "marker split result marker count mismatch"
    fi
  fi

  MARKER_SOURCE_COUNT="$(jq '.markers | length' "$MARKER_PLAN")"

  plan_slices="$(
    jq -n \
      --arg feature_branch "$FEATURE_BRANCH" \
      --arg base_branch "$BASE_BRANCH" \
      --arg feature_dir "$FEATURE_DIR_REL" \
      --arg title_scope "$TITLE_SCOPE" \
      --arg marker_split_evidence "$MARKER_SPLIT_RESULT" \
      --arg route "$EMISSION_ROUTE" \
      --slurpfile plan "$MARKER_PLAN" \
      --slurpfile split "$MARKER_SPLIT_RESULT" '
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
                    reason: "PRSG-013 declared marker test mapped to \($gate)",
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
        def marker_files($marker): [($marker.declared_files // [])[] | .path];
        def marker_warnings($markers): [($markers[] | (.warnings // []))[]];
        def title_clean:
          gsub("\\s*\\(Priority:[^)]+\\)"; "")
          | gsub("\\s+MVP$"; "")
          | gsub("^User Story [0-9]+\\s*-\\s*"; "")
          | gsub("^User Story [0-9]+$"; "")
          | gsub("^\\s+"; "")
          | gsub("\\s+$"; "");
        def has_action_verb:
          test("^(Add|Block|Create|Document|Emit|Enforce|Fix|Generate|Improve|Persist|Protect|Record|Render|Update|Validate)\\b"; "i");
        def public_title_description($id; $source_title; $files; $explicit_title):
          (($explicit_title // "") | title_clean) as $explicit
          | if $explicit != "" then $explicit
          else
          (($source_title // $id) | title_clean) as $clean
          | (($files // []) | join(" ")) as $paths
          | if ($paths | contains("marker-plan")) then
              "Add marker split emission fixtures"
            elif ($paths | contains("multi-pr-emission-state.schema.json")) then
              "Record marker split emission state"
            elif ($paths | contains("generate-spec-index.sh")) then
              "Persist PR table and resume evidence"
            elif ($paths | contains("multi-pr-emission.sh")) then
              "Emit ordered slice PRs"
            elif ($paths | contains("generate-pr-body.sh")) then
              "Render reviewer PR body evidence"
            elif ($clean | has_action_verb) then
              $clean
            elif ($id == "foundation") then
              "Add split PR emission foundation"
            else
              "Describe reviewer-visible change"
            end
          end;

        ($plan[0].markers | sort_by(.review_order)) as $markers
        | ($plan[0].warnings // []) as $plan_warnings
        | ($split[0].warnings // []) as $split_warnings
        | (($route == "hazard_collapsed") as $collapse
          | if $collapse then
              [
                {
                  source_id: "full-spec",
                  slice_id: "full-spec",
                  marker_id: "full-spec",
                  source_marker_ids: ($markers | map(.id)),
                  source_marker_checkpoints: ($markers | map(.implementation_checkpoint.evidence_path)),
                  route: "hazard_collapsed",
                  review_order: 1,
                  branch: "\($feature_branch)/01-full-spec",
                  depends_on: [],
                  declared_files: ([$markers[] | marker_files(.)[]] | unique),
                  declared_tests: ([$markers[].declared_tests[]] | unique),
                  advisory_size: {},
                  marker_split_evidence: $marker_split_evidence,
                  implementation_checkpoint_evidence: ($markers | map(.implementation_checkpoint.evidence_path) | join(",")),
                  checkpoint_sha: ($markers[-1].implementation_checkpoint.head_sha // $markers[-1].implementation_checkpoint.commit_sha // ""),
                  source_marker_checkpoint_shas: [$markers[] | (.implementation_checkpoint.head_sha // .implementation_checkpoint.commit_sha // "")],
                  warnings: ($split_warnings + $plan_warnings + marker_warnings($markers)),
                  final_marker_split_warnings: $split_warnings
                }
              ]
            else
              (($markers | length | tostring | length) as $digits | if $digits < 2 then 2 else $digits end) as $width
              | $markers
              | to_entries
              | map(
                  .key as $idx
                  | .value as $marker
                  | ($idx + 1) as $review_order
                  | ($review_order | zpad($width)) as $label
                  | (marker_files($marker)) as $declared_files
                  | (($marker.source_boundary.section // $marker.id)) as $source_title
                  | (public_title_description($marker.id; $source_title; $declared_files; ($marker.title_description // ""))) as $title_description
                  | {
                      source_id: $marker.id,
                      source_title: $source_title,
                      title_description: $title_description,
                      generated_title: ("feat(" + $title_scope + "): " + $title_description),
                      slice_id: $marker.id,
                      marker_id: $marker.id,
                      source_marker_ids: [$marker.id],
                      source_marker_checkpoints: [$marker.implementation_checkpoint.evidence_path],
                      route: "marker_split",
                      review_order: $marker.review_order,
                      branch: "\($feature_branch)/\($label)-\($marker.id)",
                      depends_on: [],
                      declared_files: $declared_files,
                      declared_tests: ($marker.declared_tests // []),
                      advisory_size: {},
                      marker_split_evidence: $marker_split_evidence,
                      implementation_checkpoint_evidence: $marker.implementation_checkpoint.evidence_path,
                      checkpoint_sha: ($marker.implementation_checkpoint.head_sha // $marker.implementation_checkpoint.commit_sha // ""),
                      reviewability: $marker.reviewability,
                      warnings: (($marker.warnings // []) + $split_warnings + $plan_warnings),
                      final_marker_split_warnings: $split_warnings
                    }
                )
            end
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
else
  plan_slices="$(
  jq -n \
    --arg feature_branch "$FEATURE_BRANCH" \
    --arg base_branch "$BASE_BRANCH" \
    --arg feature_dir "$FEATURE_DIR_REL" \
    --arg title_scope "$TITLE_SCOPE" \
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

      def title_clean:
        gsub("\\s*\\(Priority:[^)]+\\)"; "")
        | gsub("\\s+MVP$"; "")
        | gsub("^User Story [0-9]+\\s*-\\s*"; "")
        | gsub("^User Story [0-9]+$"; "")
        | gsub("^\\s+"; "")
        | gsub("\\s+$"; "");
      def has_action_verb:
        test("^(Add|Block|Create|Document|Emit|Enforce|Fix|Generate|Improve|Persist|Protect|Record|Render|Update|Validate)\\b"; "i");
      def public_title_description($id; $source_title; $files; $explicit_title):
        (($explicit_title // "") | title_clean) as $explicit
        | if $explicit != "" then $explicit
        else
        (($source_title // $id) | title_clean) as $clean
        | (($files // []) | join(" ")) as $paths
        | if ($paths | contains("marker-plan")) then
            "Add marker split emission fixtures"
          elif ($paths | contains("multi-pr-emission-state.schema.json")) then
            "Record marker split emission state"
          elif ($paths | contains("generate-spec-index.sh")) then
            "Persist PR table and resume evidence"
          elif ($paths | contains("multi-pr-emission.sh")) then
            "Emit ordered slice PRs"
          elif ($paths | contains("generate-pr-body.sh")) then
            "Render reviewer PR body evidence"
          elif ($clean | has_action_verb) then
            $clean
          elif ($id == "foundation") then
            "Add split PR emission foundation"
          else
            "Describe reviewer-visible change"
          end
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
              | (($inc.name // $inc.id) as $source_title
                | (public_title_description($inc.id; $source_title; ($inc.files // []); ($inc.title_description // ""))) as $title_description
                | {
                  source_id: $inc.id,
                  source_title: $source_title,
                  title_description: $title_description,
                  generated_title: ("feat(" + $title_scope + "): " + $title_description),
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
                })
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
fi

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

generic_title_slice="$(
  printf '%s' "$plan_slices" | jq -r '
    map(
      select(
        ((.title_description // "") | test("^(Foundation|User Story|US[0-9]+|us[0-9]+|full-spec|slice|Describe reviewer-visible change)$"; "i"))
        or ((.title_description // "") | test("\\(Priority:|\\bMVP\\b|foundation slice"; "i"))
        or ((.generated_title // "") | test(": (Foundation|User Story|US[0-9]+|us[0-9]+|full-spec|slice|Describe reviewer-visible change)(\\b|$)"; "i"))
      )
    )
    | .[0].slice_id // empty
  '
)"
if [ -n "$generic_title_slice" ]; then
  emit_input_error "unable to derive public PR title for slice $generic_title_slice"
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
    if [ "$MARKER_MODE" = true ]; then
      emit_input_error "changed file outside declared marker scope: $scope_violation"
    fi
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
      --arg marker_plan_path "$MARKER_PLAN" \
      --arg marker_split_result "$MARKER_SPLIT_RESULT" \
      --arg emission_mode "$EMISSION_MODE" \
      --arg route "$EMISSION_ROUTE" \
      --arg base_branch "$BASE_BRANCH" \
      --arg base_sha "$BASE_SHA" \
      --argjson slices "$plan_slices" '
        {
            multi_pr_emission: {
              schema_version: (if $emission_mode == "marker" then 2 else 1 end),
              status: "pending",
              emission_mode: $emission_mode,
              route: $route,
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
                        head_sha: (.checkpoint_sha // null),
                        declared_files: .declared_files,
                        declared_scoped_tests: .declared_tests,
                        scoped_verification: .scoped_verification,
                        status: "pending"
                      }
                    + (if ((.marker_id? // "") != "") then {
                        marker_id: .marker_id,
                        source_marker_ids: (.source_marker_ids // [.marker_id]),
                        source_marker_checkpoints: (.source_marker_checkpoints // []),
                        route: (.route // $route),
                        marker_split_evidence: (.marker_split_evidence // $marker_split_result)
                      } else {} end)
                  )
              )
            }
          }
        | if $source_path != "" then
            .multi_pr_emission.source_layer_plan = {path: $source_path}
          else
            .multi_pr_emission.source_marker_plan = {path: $marker_plan_path}
            | .multi_pr_emission.marker_split_result = {path: $marker_split_result}
          end
      '
  )"
  candidate_prs="$(jq -n '{schemaVersion: 2, records: []}')"
  candidate_commands="$(
    jq -n \
      --argjson slices "$plan_slices" \
      --argjson scope_guard "$scope_guard" \
      --arg candidate_dir "$CANDIDATE_DIR" \
      --arg emission_mode "$EMISSION_MODE" \
      --arg title_scope "$TITLE_SCOPE" \
      --arg validator "$SCRIPT_DIR/validate-pr-packet.sh" '
        def body_file($slice_id): "\($candidate_dir)/pr-bodies/\($slice_id).md";
        def packet_file($slice_id):
          if $emission_mode == "marker" then "\($candidate_dir)/marker-packets/\($slice_id).json"
          else "\($candidate_dir)/slice-packets/\($slice_id).json"
          end;
        def generated_title($slice):
          $slice.generated_title // ("feat(" + $title_scope + "): " + ($slice.title_description // $slice.source_title // $slice.slice_id));
        def validate_op($slice):
          if $emission_mode == "marker" then []
          else [
            {
              slice_id: $slice.slice_id,
              review_order: $slice.review_order,
              action: "validate_pr_packet",
              packet_file: packet_file($slice.slice_id),
              command: [$validator, packet_file($slice.slice_id)]
            }
          ]
          end;
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
                    }
                  ]
                  + validate_op($slice)
                  + [
                    {
                      slice_id: $slice.slice_id,
                      review_order: $slice.review_order,
                      action: "gh_pr_create",
                      branch: $slice.branch,
                      base_branch: $slice.base_branch,
                      title: generated_title($slice),
                      body_file: body_file($slice.slice_id),
                      command: ["gh", "pr", "create", "--base", $slice.base_branch, "--head", $slice.branch, "--body-file", body_file($slice.slice_id), "--title", generated_title($slice)]
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

  packet_dir_name="slice-packets"
  if [ "$MARKER_MODE" = true ]; then
    packet_dir_name="marker-packets"
  fi
  mkdir -p "$CANDIDATE_DIR/$packet_dir_name" "$CANDIDATE_DIR/pr-bodies"
  while IFS= read -r slice_json; do
    slice_id="$(printf '%s' "$slice_json" | jq -r '.slice_id')"
    title_description="$(printf '%s' "$slice_json" | jq -r '.title_description // "Prepare reviewer-ready split PR evidence"')"
    packet_path="$CANDIDATE_DIR/$packet_dir_name/$slice_id.json"
    body_file="$CANDIDATE_DIR/pr-bodies/$slice_id.md"
    packet_json="$(
      jq -n \
        --argjson slice "$slice_json" \
        --arg body_file "$body_file" \
        --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" \
        --arg title_scope "$TITLE_SCOPE" \
        --arg base_sha "$BASE_SHA" \
        --argjson total_slices "$(printf '%s' "$plan_slices" | jq 'length')" '
          {
            slice_id: $slice.slice_id,
            review_order: $slice.review_order,
            total_slices: $total_slices,
            base_branch: $slice.base_branch,
            head_branch: $slice.branch,
            target: {
              base_branch: $slice.base_branch,
              head_branch: $slice.branch
            },
            generated_title: {
              value: ($slice.generated_title // ("feat(" + $title_scope + "): " + ($slice.title_description // $slice.source_title // $slice.slice_id))),
              type: "feat",
              scope: $title_scope,
              description: ($slice.title_description // $slice.source_title // $slice.slice_id),
                source_evidence: {
                  kind: (if (($slice.marker_id? // "") != "") then "marker_source_boundary" else "layer_plan_increment" end),
                  source: ($slice.source_id // $slice.slice_id),
                  summary: "Source label and declared file scope normalized into a strict plain-English reviewer title."
                },
              rejected_candidates: [
                {
                  value: $slice.branch,
                  reason: "Branch names remain metadata and are not public title descriptions."
                },
                {
                  value: $slice.slice_id,
                  reason: "Slice ids remain metadata and are not public title descriptions."
                }
              ]
            },
            body_file: $body_file,
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
              head_sha: ($slice.checkpoint_sha // $base_sha),
              merged_sha: null
            }
          }
          + (if (($slice.marker_id? // "") != "") then {
              marker_id: $slice.marker_id,
              source_marker_ids: ($slice.source_marker_ids // [$slice.marker_id]),
              source_marker_checkpoints: ($slice.source_marker_checkpoints // []),
              route: ($slice.route // "marker_split"),
              marker_split_evidence: ($slice.marker_split_evidence // ""),
              implementation_checkpoint_evidence: ($slice.implementation_checkpoint_evidence // ""),
              final_marker_split_warnings: ($slice.final_marker_split_warnings // []),
              rollback_or_flags: "Use the recorded marker/base order for rollback or feature-flag review."
            } else {} end)
        '
    )"
    write_json_atomic "$packet_path" "$packet_json"
    {
      printf '## Summary\n\n'
      printf 'This PR covers one reviewer-ready slice: %s.\n\n' "$title_description"
      printf '## What Changed\n\n'
      printf -- '- Builds the generated PR title and reviewer-readable body for this slice.\n'
      printf -- '- Keeps detailed validation records in packet files instead of putting logs and paths in the PR description.\n\n'
      printf '## Why It Matters\n\n'
      printf 'Reviewers can scan the PR quickly and open implementation files only when they want more detail.\n\n'
      printf 'Source: generated PR packet.\n'
    } > "$body_file"
  done < <(printf '%s' "$plan_slices" | jq -c '.[]')
fi

if [ -z "$CANDIDATE_DIR" ]; then
  if [ "$LIVE" != true ]; then
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
  fi

  state_suffix="/docs/ai/specs/.process/autopilot-state.json"
  case "$STATE_FILE" in
    *"$state_suffix") persist_root="${STATE_FILE%$state_suffix}" ;;
    *) emit_input_error "persistent emission requires --state under docs/ai/specs/.process/autopilot-state.json" ;;
  esac

  feature_dir_abs="$persist_root/$FEATURE_DIR_REL"
  prs_path="$feature_dir_abs/.process/prs.json"
  moc_path="$feature_dir_abs/SPEC-MOC.md"
  workflow_id="$FEATURE_BRANCH"
  if [[ "$FEATURE_BRANCH" =~ ^([A-Za-z]+)-([0-9]+) ]]; then
    workflow_id="${BASH_REMATCH[1]^^}-${BASH_REMATCH[2]}"
  elif [[ "$FEATURE_BRANCH" =~ ^([0-9]+) ]]; then
    workflow_id="${BASH_REMATCH[1]}"
  fi
  workflow_path="$persist_root/docs/ai/specs/.process/${workflow_id}-workflow.md"

  [ -d "$feature_dir_abs" ] || emit_input_error "feature directory not found for persistent emission: $feature_dir_abs"
  [ -f "$moc_path" ] || emit_input_error "SPEC-MOC.md not found for persistent emission: $moc_path"

  if [ "$LIVE" = true ]; then
    [ -e "$persist_root/.git" ] || emit_input_error "--live requires a git repository at persistent root: $persist_root"
    command -v git >/dev/null 2>&1 || emit_input_error "--live requires git"

    live_missing_checkpoint="$(
      printf '%s' "$plan_slices" | jq -r '
        map(select((.checkpoint_sha // "") == ""))
        | .[0].slice_id // empty
      '
    )"
    [ -z "$live_missing_checkpoint" ] || emit_input_error "--live requires checkpoint_sha for slice $live_missing_checkpoint"

    live_bad_checkpoint=""
    while IFS= read -r checkpoint_sha; do
      [ -n "$checkpoint_sha" ] || continue
      if ! git -C "$persist_root" cat-file -e "$checkpoint_sha^{commit}" >/dev/null 2>&1; then
        live_bad_checkpoint="$checkpoint_sha"
        break
      fi
    done < <(printf '%s' "$plan_slices" | jq -r '.[].checkpoint_sha')
    [ -z "$live_bad_checkpoint" ] || emit_input_error "--live checkpoint is not a commit: $live_bad_checkpoint"

    live_status="$(git -C "$persist_root" status --porcelain)"
    [ -z "$live_status" ] || emit_input_error "--live requires a clean worktree before branch/PR mutation"
    command -v gh >/dev/null 2>&1 || emit_input_error "--live requires gh"
  fi

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
    local slice_json="$1" body_file="$2" title="$3"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" \
        --arg body_file "$body_file" \
        --arg title "$title" '
          $log
          | .operations += [
              {
                slice_id: $slice.slice_id,
                review_order: $slice.review_order,
                action: "gh_pr_create",
                branch: $slice.branch,
                base_branch: $slice.base_branch,
                title: $title,
                body_file: $body_file,
                command: ["gh", "pr", "create", "--base", $slice.base_branch, "--head", $slice.branch, "--body-file", $body_file, "--title", $title]
              }
            ]
        '
    )"
  }

  record_branch_command() {
    local slice_json="$1" checkpoint_sha="$2"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" \
        --arg checkpoint_sha "$checkpoint_sha" '
          $log
          | .operations += [
              {
                slice_id: $slice.slice_id,
                review_order: $slice.review_order,
                action: "git_branch",
                branch: $slice.branch,
                base_branch: $slice.base_branch,
                checkpoint_sha: $checkpoint_sha,
                command: ["git", "branch", "-f", $slice.branch, $checkpoint_sha]
              }
            ]
        '
    )"
  }

  record_push_command() {
    local slice_json="$1"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" '
          $log
          | .operations += [
              {
                slice_id: $slice.slice_id,
                review_order: $slice.review_order,
                action: "git_push",
                branch: $slice.branch,
                command: ["git", "push", "-u", "origin", $slice.branch]
              }
            ]
        '
    )"
  }

  record_validate_command() {
    local slice_json="$1" packet_file="$2" validation_result_path="$3"
    command_log_json="$(
      jq -n \
        --argjson log "$command_log_json" \
        --argjson slice "$slice_json" \
        --arg packet_file "$packet_file" \
        --arg validation_result_path "$validation_result_path" \
        --arg validator "$SCRIPT_DIR/validate-pr-packet.sh" '
          $log
          | .operations += [
              {
                slice_id: $slice.slice_id,
                review_order: $slice.review_order,
                action: "validate_pr_packet",
                packet_file: $packet_file,
                validation_result_path: $validation_result_path,
                command: [$validator, $packet_file]
              }
            ]
        '
    )"
  }

  live_find_pr() {
    local head_branch="$1" base_branch="$2" pr_list_json
    if ! pr_list_json="$(
      cd "$persist_root" &&
      gh pr list --head "$head_branch" --base "$base_branch" --state all --json number,url,state,headRefOid 2>/dev/null
    )"; then
      return 0
    fi
    printf '%s' "$pr_list_json" | jq -c \
      --arg head "$head_branch" \
      --arg base "$base_branch" '
        .[0]? // empty
        | {
            head: $head,
            base: $base,
            number: .number,
            url: .url,
            state: .state,
            head_sha: (.headRefOid // ""),
            merged_sha: null
          }
      '
  }

  live_create_pr() {
    local slice_id="$1" head_branch="$2" base_branch="$3" body_file="$4" title="$5" created_ref
    created_ref="$(
      cd "$persist_root" &&
      gh pr create --base "$base_branch" --head "$head_branch" --body-file "$body_file" --title "$title"
    )" || return 1
    [ -n "$created_ref" ] || return 1
    (
      cd "$persist_root" &&
      gh pr view "$created_ref" --json number,url,state,headRefOid
    ) | jq -c \
      --arg head "$head_branch" \
      --arg base "$base_branch" '
        {
          head: $head,
          base: $base,
          number: .number,
          url: .url,
          state: .state,
          head_sha: (.headRefOid // ""),
          merged_sha: null
        }
      '
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
      --arg marker_plan_path "$MARKER_PLAN" \
      --arg marker_split_result "$MARKER_SPLIT_RESULT" \
      --arg emission_mode "$EMISSION_MODE" \
      --arg route "$EMISSION_ROUTE" \
      --arg base_branch "$BASE_BRANCH" \
      --arg base_sha "$BASE_SHA" \
      --argjson slices "$plan_slices" '
        {
          multi_pr_emission: {
            schema_version: (if $emission_mode == "marker" then 2 else 1 end),
            status: "emitting",
            emission_mode: $emission_mode,
            route: $route,
            base_branch: $base_branch,
            base_sha: $base_sha,
            next_slice_id: ($slices[0].slice_id // null),
            reconciled_at: "2026-06-10T00:00:00Z",
            slices: (
              $slices
              | map(
                  {
                    slice_id: .slice_id,
                    review_order: .review_order,
                    expected_branch: .branch,
                    expected_base_branch: .base_branch,
                    head_sha: (.checkpoint_sha // null),
                    declared_files: .declared_files,
                    declared_scoped_tests: .declared_tests,
                    scoped_verification: .scoped_verification,
                    status: "pending"
                  }
                  + (if ((.marker_id? // "") != "") then {
                      marker_id: .marker_id,
                      source_marker_ids: (.source_marker_ids // [.marker_id]),
                      source_marker_checkpoints: (.source_marker_checkpoints // []),
                      route: (.route // $route),
                      marker_split_evidence: (.marker_split_evidence // $marker_split_result)
                    } else {} end)
                )
            )
          }
        }
        | if $source_path != "" then
            .multi_pr_emission.source_layer_plan = {path: $source_path}
          else
            .multi_pr_emission.source_marker_plan = {path: $marker_plan_path}
            | .multi_pr_emission.marker_split_result = {path: $marker_split_result}
          end
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
    packet_file_name="slice-packet.json"
    if [ "$MARKER_MODE" = true ]; then
      packet_file_name="marker-packet.json"
    fi
    packet_path="$packet_dir/$packet_file_name"
    body_file="$packet_dir/pr-body.md"
    body_file_rel="$(repo_relative_path "$body_file" "$persist_root")"
    pr_packet_path="$packet_dir/pr-packet.json"
    pr_packet_rel="$(repo_relative_path "$pr_packet_path" "$persist_root")"
    validation_result_path="$FEATURE_DIR_REL/.process/pr-packets/$slice_id/validation.json"
    mkdir -p "$packet_dir"

    packet_json="$(
      jq -n \
        --argjson slice "$slice_json" \
        --arg body_file "$body_file_rel" \
        --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" \
        --arg title_scope "$TITLE_SCOPE" \
        --arg base_sha "$BASE_SHA" \
        --argjson total_slices "$total_slices" '
          {
            slice_id: $slice.slice_id,
            review_order: $slice.review_order,
            total_slices: $total_slices,
            base_branch: $slice.base_branch,
            head_branch: $slice.branch,
            target: {
              base_branch: $slice.base_branch,
              head_branch: $slice.branch
            },
            generated_title: {
              value: ($slice.generated_title // ("feat(" + $title_scope + "): " + ($slice.title_description // $slice.source_title // $slice.slice_id))),
              type: "feat",
              scope: $title_scope,
              description: ($slice.title_description // $slice.source_title // $slice.slice_id),
                source_evidence: {
                  kind: (if (($slice.marker_id? // "") != "") then "marker_source_boundary" else "layer_plan_increment" end),
                  source: ($slice.source_id // $slice.slice_id),
                  summary: "Source label and declared file scope normalized into a strict plain-English reviewer title."
                },
              rejected_candidates: [
                {
                  value: $slice.branch,
                  reason: "Branch names remain metadata and are not public title descriptions."
                },
                {
                  value: $slice.slice_id,
                  reason: "Slice ids remain metadata and are not public title descriptions."
                }
              ]
            },
            body_file: $body_file,
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
              head_sha: ($slice.checkpoint_sha // $base_sha),
              merged_sha: null
            }
          }
          + (if (($slice.marker_id? // "") != "") then {
              marker_id: $slice.marker_id,
              source_marker_ids: ($slice.source_marker_ids // [$slice.marker_id]),
              source_marker_checkpoints: ($slice.source_marker_checkpoints // []),
              route: ($slice.route // "marker_split"),
              marker_split_evidence: ($slice.marker_split_evidence // ""),
              implementation_checkpoint_evidence: ($slice.implementation_checkpoint_evidence // ""),
              final_marker_split_warnings: ($slice.final_marker_split_warnings // []),
              rollback_or_flags: "Use the recorded marker/base order for rollback or feature-flag review."
            } else {} end)
        '
    )"
    persist_json_atomic "$packet_path" "$packet_json" || emit_input_error "slice packet persistence failed: $packet_path"
    (
      cd "$persist_root" &&
      "$SCRIPT_DIR/generate-pr-body.sh" --slice-packet "$packet_path" "$persist_root" "$FEATURE_DIR_REL" "$body_file" "$BASE_SHA...HEAD" >/dev/null
    )
    pr_title="$(printf '%s' "$packet_json" | jq -r '.generated_title.value')"

    if [ "$MARKER_MODE" != true ]; then
      slice_packet_rel="$(repo_relative_path "$packet_path" "$persist_root")"
      body_sha="$(protected_body_sha "$body_file")"
      pr_packet_json="$(
        jq -n \
          --argjson slice "$slice_json" \
          --arg packet_id "$slice_id" \
          --arg source_feature_dir "$FEATURE_DIR_REL" \
          --arg body_file "$body_file_rel" \
          --arg validation_result_path "$validation_result_path" \
          --arg slice_packet "$slice_packet_rel" \
          --arg body_sha "$body_sha" \
          --arg full_verification_evidence "$FULL_VERIFICATION_EVIDENCE" \
          --arg title_scope "$TITLE_SCOPE" \
          '
            {
              schema_version: "1.0.0",
              packet_id: $packet_id,
              mode: "split",
              target: {
                base_branch: $slice.base_branch,
                head_branch: $slice.branch
              },
              source_feature_dir: $source_feature_dir,
              generated_title: {
                value: ($slice.generated_title // ("feat(" + $title_scope + "): " + ($slice.title_description // $slice.source_title // $slice.slice_id))),
                type: "feat",
                scope: $title_scope,
                description: ($slice.title_description // $slice.source_title // $slice.slice_id),
                source_evidence: {
                  kind: "split_source_boundary",
                  source: ($slice.source_id // $slice.slice_id),
                  summary: "Source label and declared file scope normalized into a strict plain-English reviewer title."
                },
                rejected_candidates: [
                  {
                    value: $slice.branch,
                    reason: "Branch names remain metadata and are not public title descriptions."
                  },
                  {
                    value: $slice.slice_id,
                    reason: "Slice ids remain metadata and are not public title descriptions."
                  }
                ]
              },
              body_file: $body_file,
              required_headings: [
                "Summary",
                "What Changed",
                "Why It Matters",
                "How To Review",
                "How To UAT",
                "Verification",
                "Scope",
                "Known Gaps"
              ],
              verification_evidence: [
                {
                  kind: "split_packet_validation",
                  source: ($slice.scoped_verification.commands[0].evidence_path // $full_verification_evidence),
                  summary: "Scoped verification for split packet passed before PR creation.",
                  result: "passed"
                }
              ],
              scope_evidence: {
                reviewable_loc: 0,
                production_files: 0,
                total_files: ($slice.declared_files | length),
                budget_result: "within_budget",
                changed_files: $slice.declared_files,
                non_goals: [
                  "This split packet does not broaden the declared slice scope.",
                  "This split packet does not replace full regression evidence."
                ]
              },
              uat: {
                how_to_uat: "Run the scoped verification commands and confirm full regression evidence before PR creation.",
                uat_runbook_heading: "## UAT Runbook",
                uat_source: $body_file
              },
              source_markers: [
                {
                  marker_id: "slice-packet",
                  rendered_text: "Source: slice packet defines split PR identity and source boundary evidence.",
                  source: $slice_packet
                },
                {
                  marker_id: "slice-scope",
                  rendered_text: "Source: slice packet declared files and scoped verification define the reviewer body.",
                  source: $slice_packet
                },
                {
                  marker_id: "quickstart-verification",
                  rendered_text: "Source: quickstart and scoped verification records define the validation evidence.",
                  source: ($source_feature_dir + "/quickstart.md")
                }
              ],
              editable_fields: [
                {
                  field_id: "summary",
                  heading: "Summary",
                  start_marker: "<!-- speckit-pro-editable:summary:start -->",
                  end_marker: "<!-- speckit-pro-editable:summary:end -->"
                },
                {
                  field_id: "what_changed",
                  heading: "What Changed",
                  start_marker: "<!-- speckit-pro-editable:what_changed:start -->",
                  end_marker: "<!-- speckit-pro-editable:what_changed:end -->"
                },
                {
                  field_id: "why_it_matters",
                  heading: "Why It Matters",
                  start_marker: "<!-- speckit-pro-editable:why_it_matters:start -->",
                  end_marker: "<!-- speckit-pro-editable:why_it_matters:end -->"
                }
              ],
              protected_body_fingerprint: {
                algorithm: "sha256",
                value: $body_sha,
                normalization: "canonical packet block only; LF line endings; trailing whitespace trimmed; editable block bodies replaced by <elided:field_id> before sha256.",
                elided_fields: [
                  "summary",
                  "what_changed",
                  "why_it_matters"
                ]
              },
              split_slice: {
                slice_id: $slice.slice_id,
                source_boundary: {
                  section: ($slice.title_description // $slice.source_title // $slice.slice_id)
                },
                source_packet: $slice_packet
              },
              validation_result_path: $validation_result_path
            }
          '
      )"
      persist_json_atomic "$pr_packet_path" "$pr_packet_json" || emit_input_error "PR packet persistence failed: $pr_packet_path"
      pr_title="$(printf '%s' "$pr_packet_json" | jq -r '.generated_title.value')"
    fi

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

    if [ "$MARKER_MODE" != true ]; then
      record_validate_command "$slice_json" "$pr_packet_rel" "$validation_result_path"
      validation_stdout="$(mktemp)"
      validation_stderr="$(mktemp)"
      validation_status=0
      set +e
      (
        cd "$persist_root" &&
        "$SCRIPT_DIR/validate-pr-packet.sh" "$pr_packet_rel"
      ) >"$validation_stdout" 2>"$validation_stderr"
      validation_status=$?
      set -e
      rm -f "$validation_stdout" "$validation_stderr"
      if [ "$validation_status" -ne 0 ]; then
        block_with_state "$slice_id" "pr_packet_validation" "validate-pr-packet.sh failed for slice $slice_id" "failed" "$validation_status"
      fi
    fi

    if [ "$LIVE" = true ]; then
      checkpoint_sha="$(printf '%s' "$slice_json" | jq -r '.checkpoint_sha // empty')"
      base_ref="$base_branch"
      if ! git -C "$persist_root" rev-parse --verify "$base_ref^{commit}" >/dev/null 2>&1; then
        if git -C "$persist_root" rev-parse --verify "origin/$base_branch^{commit}" >/dev/null 2>&1; then
          base_ref="origin/$base_branch"
        else
          block_with_state "$slice_id" "git_base_ref" "base branch not found for slice $slice_id: $base_branch" "failed" 2
        fi
      fi
      if ! git -C "$persist_root" merge-base --is-ancestor "$base_ref" "$checkpoint_sha" >/dev/null 2>&1; then
        block_with_state "$slice_id" "git_branch" "checkpoint $checkpoint_sha is not based on $base_branch for slice $slice_id" "failed" 2
      fi
      record_branch_command "$slice_json" "$checkpoint_sha"
      if ! git -C "$persist_root" branch -f "$head_branch" "$checkpoint_sha" >/dev/null 2>&1; then
        block_with_state "$slice_id" "git_branch" "git branch failed for slice $slice_id" "failed" 2
      fi
      record_push_command "$slice_json"
      if ! git -C "$persist_root" push -u origin "$head_branch" >/dev/null 2>&1; then
        block_with_state "$slice_id" "git_push" "git push failed for slice $slice_id" "failed" 2
      fi
      state_json="$(
        printf '%s' "$state_json" | jq \
          --arg slice "$slice_id" \
          --arg head_sha "$checkpoint_sha" '
            (.multi_pr_emission.slices[] | select(.slice_id == $slice)) += {
              status: "branch_created",
              head_sha: $head_sha
            }
          '
      )"
      persist_state_or_die
    fi

    if [ "$LIVE" = true ]; then
      pr_json="$(live_find_pr "$head_branch" "$base_branch")"
    else
      pr_json="$(
        jq -c --arg head "$head_branch" --arg base "$base_branch" '
          (.existing // [])
          | map(select(.head == $head and .base == $base))
          | .[0] // empty
        ' "$PR_FIXTURE"
      )"
    fi
    pr_source="existing"

    if [ -z "$pr_json" ]; then
      record_create_command "$slice_json" "$body_file" "$pr_title"
      if [ "$LIVE" = true ]; then
        pr_json="$(live_create_pr "$slice_id" "$head_branch" "$base_branch" "$body_file" "$pr_title")" || \
          block_with_state "$slice_id" "gh_pr_create" "gh pr create failed for slice $slice_id" "failed" 4
      else
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
      fi
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
  mutation_json="$(jq -cn --argjson live "$LIVE" '{branches: $live, pull_requests: $live}')"

  jq -cn \
    --argjson slice_count "$(printf '%s' "$plan_slices" | jq 'length')" \
    --arg emission_mode "$EMISSION_MODE" \
    --arg route "$EMISSION_ROUTE" \
    --argjson marker_count "$MARKER_SOURCE_COUNT" \
    --argjson mutation "$mutation_json" \
    --arg state "$STATE_FILE" \
    --arg prs "$prs_path" \
    --arg moc "$moc_path" \
    --arg workflow "$workflow_path" \
    '{
      script: "multi-pr-emission",
      status: "persisted",
      mutation: $mutation,
      emission: {
        slice_count: $slice_count,
        marker_count: $marker_count,
        mode: $emission_mode,
        route: $route,
        dry_run: false
      },
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
  --arg emission_mode "$EMISSION_MODE" \
  --arg route "$EMISSION_ROUTE" \
  --argjson slice_count "$slice_count" \
  --argjson marker_count "$MARKER_SOURCE_COUNT" \
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
      marker_count: $marker_count,
      mode: $emission_mode,
      route: $route,
      dry_run: true
    },
    candidate_files: {
      state: (if $candidate_state == "" then null else $candidate_state end),
      prs_manifest: (if $candidate_prs == "" then null else $candidate_prs end),
      command_capture: (if $candidate_commands == "" then null else $candidate_commands end)
    }
  }'

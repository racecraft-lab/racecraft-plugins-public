#!/usr/bin/env bash
# o5-topology.sh - Validate O5 parent manifests and compute child rollup status.

set -euo pipefail

usage() {
  printf 'Usage: o5-topology.sh <specs/<parent-branch>|specs/<parent-branch>/o5-parent-manifest.json>\n' >&2
}

emit_error() {
  local message="$1"
  jq -cn --arg error "$message" '{error:$error}'
  exit 2
}

repo_relative_path() {
  local raw="$1" abs="$2"
  case "$abs" in
    */specs/*) printf 'specs/%s\n' "${abs#*/specs/}" ;;
    *) printf '%s\n' "${raw#./}" ;;
  esac
}

repo_root_for_manifest() {
  local abs="$1"
  case "$abs" in
    */specs/*) printf '%s\n' "${abs%%/specs/*}" ;;
    *) git rev-parse --show-toplevel 2>/dev/null || pwd -P ;;
  esac
}

add_problem() {
  local code="$1" message="$2" path="${3:-}" child_id="${4:-}"
  jq -cn \
    --arg code "$code" \
    --arg message "$message" \
    --arg path "$path" \
    --arg child_id "$child_id" \
    '{
      code: $code,
      message: $message
    }
    + (if $path == "" then {} else {path: $path} end)
    + (if $child_id == "" then {} else {child_id: $child_id} end)' >> "$PROBLEMS_TMP"
}

normalize_status() {
  local raw="$1"
  raw="$(printf '%s' "$raw" | tr '[:upper:]' '[:lower:]' | tr '-' '_')"
  case "$raw" in
    blocked) printf 'blocked' ;;
    failed|fail) printf 'failed' ;;
    in_progress|progress|active) printf 'in_progress' ;;
    pending|"") printf 'pending' ;;
    complete|completed|done) printf 'complete' ;;
    archived|archive) printf 'archived' ;;
    *) printf 'missing-state' ;;
  esac
}

read_moc_status() {
  local moc="$1" raw
  raw="$(awk -F: '
    /^status:/ {
      val=$0
      sub(/^status:[[:space:]]*/, "", val)
      gsub(/#.*/, "", val)
      gsub(/["'\'']/, "", val)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", val)
      print val
      exit
    }
  ' "$moc" 2>/dev/null || true)"
  normalize_status "$raw"
}

child_status() {
  local child_path="$1" child_dir="$ROOT/$child_path" moc="$ROOT/$child_path/SPEC-MOC.md"
  local gate="$ROOT/$child_path/.process/final-reviewability/gate-state.json"
  if [ ! -d "$child_dir" ]; then
    printf 'missing\tmissing child directory'
    return
  fi
  if [ -r "$gate" ] && jq -e '.status == "block"' "$gate" >/dev/null 2>&1; then
    printf 'blocked\tfinal reviewability gate'
    return
  fi
  if [ ! -f "$moc" ]; then
    printf 'missing-state\tmissing SPEC-MOC status'
    return
  fi
  local status
  status="$(read_moc_status "$moc")"
  if [ "$status" = "missing-state" ]; then
    printf 'missing-state\tSPEC-MOC status'
  else
    printf '%s\tSPEC-MOC status' "$status"
  fi
}

INPUT="${1:-}"
[ -n "$INPUT" ] || { usage; emit_error "missing O5 parent path"; }

if [ -d "$INPUT" ]; then
  MANIFEST="$INPUT/o5-parent-manifest.json"
else
  MANIFEST="$INPUT"
fi

[ -r "$MANIFEST" ] || emit_error "O5 parent manifest not readable: $MANIFEST"
jq -e 'type == "object"' "$MANIFEST" >/dev/null 2>&1 || emit_error "O5 parent manifest is not a JSON object"

MANIFEST_DIR="$(cd "$(dirname "$MANIFEST")" && pwd -P)"
MANIFEST_ABS="$MANIFEST_DIR/$(basename "$MANIFEST")"
MANIFEST_REL="$(repo_relative_path "$MANIFEST" "$MANIFEST_ABS")"
ROOT="$(repo_root_for_manifest "$MANIFEST_ABS")"

PROBLEMS_TMP="$(mktemp "${TMPDIR:-/tmp}/o5-problems.XXXXXX")"
CHILDREN_TMP="$(mktemp "${TMPDIR:-/tmp}/o5-children.XXXXXX")"
cleanup() {
  rm -f "$PROBLEMS_TMP" "$CHILDREN_TMP"
}
trap cleanup EXIT

if ! jq -e '
  .schemaVersion == 1
  and .kind == "o5_parent_manifest"
  and (.parent | type == "object")
  and (.children | type == "array")
  and (.sharedDesignConcept | type == "string")
  and (.sharedRetrospective == null or (.sharedRetrospective | type == "string"))
' "$MANIFEST" >/dev/null 2>&1; then
  add_problem "invalid_manifest_shape" "manifest must match O5 parent manifest base shape" "$MANIFEST_REL"
fi

parent_branch="$(jq -r '.parent.branch // ""' "$MANIFEST")"
parent_path="$(jq -r '.parent.path // ""' "$MANIFEST")"
expected_parent_path="specs/$parent_branch"
expected_manifest_path="$expected_parent_path/o5-parent-manifest.json"

if [ -n "$parent_branch" ] && [ "$parent_path" != "$expected_parent_path" ]; then
  add_problem "parent_path_mismatch" "parent.path must equal specs/<parent.branch>" "$parent_path"
fi
if [ -n "$parent_branch" ] && [ "$MANIFEST_REL" != "$expected_manifest_path" ]; then
  add_problem "manifest_location_mismatch" "manifest must live at specs/<parent.branch>/o5-parent-manifest.json" "$MANIFEST_REL"
fi

child_count="$(jq -r '(.children // []) | length' "$MANIFEST")"
if [ "$child_count" -eq 0 ]; then
  add_problem "zero_children" "O5 parent manifest must declare at least one child" "$parent_path"
fi

jq -r '(.children // [])[]?.id // empty' "$MANIFEST" | sort | uniq -d | while IFS= read -r duplicate_id; do
  [ -n "$duplicate_id" ] && add_problem "duplicate_child_id" "child IDs must be unique" "" "$duplicate_id"
done

if [ "$child_count" -gt 0 ]; then
  i=0
  while [ "$i" -lt "$child_count" ]; do
    child_json="$(jq -c --argjson i "$i" '.children[$i]' "$MANIFEST")"
    child_id="$(printf '%s' "$child_json" | jq -r '.id // ""')"
    child_branch="$(printf '%s' "$child_json" | jq -r '.branch // ""')"
    child_path="$(printf '%s' "$child_json" | jq -r '.path // ""')"
    child_title="$(printf '%s' "$child_json" | jq -r '.title // ""')"
    expected_child_path="specs/$child_branch"

    if [ -n "$child_branch" ] && [ "$child_path" != "$expected_child_path" ]; then
      add_problem "child_path_mismatch" "child.path must equal specs/<child.branch>" "$child_path" "$child_id"
    fi
    case "$child_path" in
      specs/*/*) add_problem "nested_child_path" "O5 child paths must be flat specs/<child-branch> siblings" "$child_path" "$child_id" ;;
      specs/*) ;;
      *) add_problem "invalid_child_path" "O5 child path must be under specs/" "$child_path" "$child_id" ;;
    esac
    if [ ! -d "$ROOT/$child_path" ]; then
      add_problem "missing_child" "declared child spec directory does not exist" "$child_path" "$child_id"
    fi

    depends_json="$(printf '%s' "$child_json" | jq -c '.dependsOn // []')"
    printf '%s' "$depends_json" | jq -r '.[]?' | while IFS= read -r dep; do
      dep_index="$(jq -r --arg dep "$dep" '(.children // [] | map(.id) | index($dep)) // -1' "$MANIFEST")"
      if [ "$dep_index" -lt 0 ]; then
        add_problem "unknown_dependency" "dependsOn references an unknown child ID" "$child_path" "$child_id"
      elif [ "$dep_index" -ge "$i" ]; then
        add_problem "later_dependency" "dependsOn must reference only earlier siblings; later/self dependencies can form cycles" "$child_path" "$child_id"
      fi
    done

    status_pair="$(child_status "$child_path")"
    status="${status_pair%%	*}"
    status_source="${status_pair#*	}"
    jq -cn \
      --arg id "$child_id" \
      --arg branch "$child_branch" \
      --arg path "$child_path" \
      --arg title "$child_title" \
      --arg status "$status" \
      --arg status_source "$status_source" \
      --argjson depends_on "$depends_json" \
      '{
        id: $id,
        branch: $branch,
        path: $path,
        title: $title,
        dependsOn: $depends_on,
        status: $status,
        statusSource: $status_source
      }' >> "$CHILDREN_TMP"

    i=$((i + 1))
  done
fi

problems_json="$(jq -s . "$PROBLEMS_TMP")"
children_json="$(jq -s . "$CHILDREN_TMP")"
problem_count="$(printf '%s' "$problems_json" | jq -r 'length')"

if [ "$problem_count" -gt 0 ]; then
  topology_status="invalid"
  computed_status="invalid_topology"
else
  topology_status="valid"
  computed_status="$(printf '%s' "$children_json" | jq -r '
    if any(.status == "blocked") then "blocked"
    elif any(.status == "failed") then "failed"
    elif any(.status == "in_progress") then "in_progress"
    elif any(.status == "pending" or .status == "missing-state") then "pending"
    else "complete"
    end
  ')"
fi

declared_status="$(jq -r '.declaredRollupStatus // empty' "$MANIFEST")"
declared_drift=false
if [ -n "$declared_status" ] && [ "$declared_status" != "$computed_status" ]; then
  declared_drift=true
  add_problem "declared_rollup_drift" "declaredRollupStatus does not match computedStatus" "$MANIFEST_REL"
  problems_json="$(jq -s . "$PROBLEMS_TMP")"
fi

jq -cn \
  --arg topology_status "$topology_status" \
  --arg computed_status "$computed_status" \
  --argjson declared_status "$(if [ -n "$declared_status" ]; then printf '%s' "$declared_status" | jq -R .; else printf 'null'; fi)" \
  --argjson declared_drift "$declared_drift" \
  --arg manifest "$MANIFEST_REL" \
  --argjson parent "$(jq -c '.parent // {}' "$MANIFEST")" \
  --argjson children "$children_json" \
  --argjson problems "$problems_json" \
  '{
    schemaVersion: 1,
    kind: "o5_topology_rollup",
    topologyStatus: $topology_status,
    computedStatus: $computed_status,
    declaredRollupStatus: $declared_status,
    declaredStatusDrift: $declared_drift,
    manifest: $manifest,
    parent: $parent,
    children: $children,
    problems: $problems
  }'

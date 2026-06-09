#!/usr/bin/env bash
# migrate-structure.sh - PRSG-011 repository structure migration.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GEN="$SCRIPT_DIR/generate-spec-index.sh"
PROCESS_RULE='**/.process/** linguist-generated=true'

# shellcheck source=lib/moc-id-normalize.sh
source "$SCRIPT_DIR/lib/moc-id-normalize.sh"
# shellcheck source=lib/moc-frontmatter.sh
source "$SCRIPT_DIR/lib/moc-frontmatter.sh"

MODE=""
REPO_ROOT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      [ -z "$MODE" ] || { printf 'migrate-structure.sh: specify exactly one mode\n' >&2; exit 2; }
      MODE="dry-run"
      ;;
    --apply)
      [ -z "$MODE" ] || { printf 'migrate-structure.sh: specify exactly one mode\n' >&2; exit 2; }
      MODE="apply"
      ;;
    --repo-root)
      shift
      [ $# -gt 0 ] || { printf 'migrate-structure.sh: --repo-root requires a value\n' >&2; exit 2; }
      REPO_ROOT="$1"
      ;;
    -h|--help)
      printf 'Usage: migrate-structure.sh (--dry-run|--apply) [--repo-root <path>]\n'
      exit 0
      ;;
    *)
      printf 'migrate-structure.sh: unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

[ -n "$MODE" ] || { printf 'migrate-structure.sh: specify exactly one mode\n' >&2; exit 2; }
if [ -z "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd -P)"
else
  REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)" || { printf 'migrate-structure.sh: invalid repo root\n' >&2; exit 2; }
fi
[ -d "$REPO_ROOT" ] || { printf 'migrate-structure.sh: repo root is not a directory: %s\n' "$REPO_ROOT" >&2; exit 2; }
git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  printf 'migrate-structure.sh: repo root is not inside a git worktree: %s\n' "$REPO_ROOT" >&2
  exit 2
}

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/migrate-structure.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
ITEMS_FILE="$TMP_DIR/items.jsonl"
: > "$ITEMS_FILE"

backup_stamp="${SPECKIT_MIGRATION_BACKUP_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
backup_root="${SPECKIT_MIGRATION_BACKUP_ROOT:-/tmp}"
backup_path="$backup_root/speckit-migration-backup-$backup_stamp"
backup_created=false

add_item() {
  local action="$1" path="${2:-}" reason="${3:-}" target="${4:-}" source="${5:-}" tier="${6:-50}"
  jq -cn \
    --arg action "$action" \
    --arg path "$path" \
    --arg reason "$reason" \
    --arg target "$target" \
    --arg source "$source" \
    --argjson tier "$tier" \
    '{
      tier: $tier,
      action: $action,
      path: $path,
      reason: $reason,
      target: $target,
      source: $source
    } | with_entries(select(.value != ""))' >> "$ITEMS_FILE"
}

json_array_from_lines() {
  jq -Rsc 'split("\n") | map(select(length > 0))'
}

marker_current() {
  local marker="$REPO_ROOT/.specify/structure-version.json"
  [ -r "$marker" ] || return 1
  jq -e '(.structureVersion | type == "number") and (.structureVersion >= 1) and (.structureVersion == (.structureVersion | floor))' \
    "$marker" >/dev/null 2>&1
}

active_feature_json() {
  local feature="$REPO_ROOT/.specify/feature.json"
  if [ ! -e "$feature" ]; then
    jq -cn '{state:"absent", path:null, reason:"feature_json_missing"}'
    return 0
  fi

  local raw
  raw="$(jq -er '.feature_directory | select(type == "string" and length > 0)' "$feature" 2>/dev/null || true)"
  if [ -z "$raw" ]; then
    jq -cn '{state:"invalid", path:null, reason:"feature_directory_invalid"}'
    return 0
  fi

  local candidate parent resolved
  case "$raw" in
    /*) candidate="$raw" ;;
    *) candidate="$REPO_ROOT/$raw" ;;
  esac
  if [ -e "$candidate" ]; then
    resolved="$(cd "$candidate" && pwd -P)" || resolved=""
  else
    parent="$(dirname "$candidate")"
    if [ -d "$parent" ]; then
      resolved="$(cd "$parent" && pwd -P)/$(basename "$candidate")"
    else
      resolved=""
    fi
  fi

  case "$resolved" in
    "$REPO_ROOT"|"$REPO_ROOT"/*)
      jq -cn --arg path "$raw" '{state:"valid", path:$path, reason:null}'
      ;;
    *)
      jq -cn --arg path "$raw" '{state:"invalid", path:$path, reason:"feature_directory_outside_repo"}'
      ;;
  esac
}

out_of_scope_reason() {
  local id="$1" first
  if [[ "$id" =~ ^[0-9]{4}($|-) ]]; then
    printf 'date_named_legacy_namespace'
    return 0
  fi
  first="${id%%-*}"
  if [[ "$first" =~ ^[A-Za-z]+$ ]] && [ "$first" != "prsg" ] && [ "$first" != "PRSG" ] && [ "$first" != "spec" ] && [ "$first" != "SPEC" ]; then
    printf 'non_speckit_namespace'
    return 0
  fi
  return 1
}

slugify_heading() {
  tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

is_active_candidate() {
  local rel="$1" active_path="$2" active_base
  [ -n "$active_path" ] || return 1
  active_base="$(basename "$active_path")"
  [ "$rel" = "$active_path" ] && return 0
  moc_id_match "$active_base" "$(basename "$rel")"
}

generator_current() {
  local rc=0
  "$GEN" --check "$REPO_ROOT" >/dev/null 2>"$TMP_DIR/generator-check.err" || rc=$?
  [ "$rc" -eq 0 ]
}

collect_candidates() {
  local active_path="$1" nav_current="$2" specs_dir="$REPO_ROOT/specs"
  [ -d "$specs_dir" ] || return 0

  local d branch rel reason moc target action
  while IFS= read -r d; do
    [ -n "$d" ] || continue
    branch="$(basename "$d")"
    rel="specs/$branch"
    reason="$(out_of_scope_reason "$branch" || true)"
    if [ -n "$reason" ]; then
      add_item "skipped_out_of_scope" "$rel" "$reason" "" "" 20
      continue
    fi
    if is_active_candidate "$rel" "$active_path"; then
      add_item "skipped_frozen_in_flight" "$rel" "" "" "" 20
      continue
    fi

    if [ "$nav_current" = "true" ]; then
      continue
    fi

    moc="$d/SPEC-MOC.md"
    if [ -f "$moc" ] && moc_is_gated "$moc"; then
      target="$rel/SPEC-MOC.md"
    else
      target="$rel/spec.md"
    fi
    action="generated_update"
    add_item "$action" "$target" "" "" "" 30
  done < <(find "$specs_dir" -mindepth 1 -maxdepth 1 -type d | LC_ALL=C sort)

  local memory="$REPO_ROOT/.specify/memory/spec.md"
  [ -f "$memory" ] || return 0
  local heading slug
  while IFS= read -r heading; do
    heading="${heading### }"
    heading="${heading## }"
    [ -n "$heading" ] || continue
    slug="$(printf '%s' "$heading" | slugify_heading)"
    reason="$(out_of_scope_reason "$slug" || true)"
    if [ -n "$reason" ]; then
      add_item "skipped_out_of_scope" ".specify/memory/spec.md#$slug" "$reason" "" "" 20
      continue
    fi
    [ "$nav_current" = "true" ] && continue
    add_item "generated_update" ".specify/memory/spec.md#$slug" "" "" "" 30
  done < <(grep -E '^##[[:space:]]+' "$memory" 2>/dev/null || true)
}

ensure_process_rule() {
  local file="$REPO_ROOT/.gitattributes" tmp="$TMP_DIR/gitattributes"
  if [ -f "$file" ]; then
    grep -vxF "$PROCESS_RULE" "$file" > "$tmp" 2>/dev/null || true
  else
    : > "$tmp"
  fi
  printf '%s\n' "$PROCESS_RULE" >> "$tmp"
  mv "$tmp" "$file"
}

deboilerplate_roadmap() {
  local file="$REPO_ROOT/docs/ai/specs/pr-size-governance-technical-roadmap.md" tmp="$TMP_DIR/roadmap"
  [ -f "$file" ] || return 0
  grep -v -E 'split exception|transition exception|ratified exception' "$file" > "$tmp" 2>/dev/null || true
  mv "$tmp" "$file"
}

create_backup() {
  mkdir -p "$backup_path" || return 1
  [ -e "$REPO_ROOT/.specify" ] && cp -R "$REPO_ROOT/.specify" "$backup_path/.specify" 2>/dev/null || true
  [ -e "$REPO_ROOT/docs/ai/specs" ] && mkdir -p "$backup_path/docs/ai" && cp -R "$REPO_ROOT/docs/ai/specs" "$backup_path/docs/ai/specs" 2>/dev/null || true
  [ -e "$REPO_ROOT/specs" ] && cp -R "$REPO_ROOT/specs" "$backup_path/specs" 2>/dev/null || true
}

emit_report() {
  local status="$1" active_json="$2" dirty_json="$3" exit_code="$4" recovery_available="${5:-false}" recovery_hint="${6:-null}"
  local items_json backup_json recovery_json
  items_json="$(jq -cs 'sort_by(.tier, .action, (.path // .target // .id // ""), (.reason // "")) | map(del(.tier))' "$ITEMS_FILE")"
  backup_json="$(jq -cn --arg path "$backup_path" --argjson created "$backup_created" '{path:$path, created:$created}')"
  if [ "$recovery_hint" = "null" ]; then
    recovery_json="$(jq -cn --argjson available "$recovery_available" '{available:$available, hint:null}')"
  else
    recovery_json="$(jq -cn --argjson available "$recovery_available" --arg hint "$recovery_hint" '{available:$available, hint:$hint}')"
  fi
  jq -cn \
    --arg script "migrate-structure" \
    --arg mode "$MODE" \
    --arg repo_root "$REPO_ROOT" \
    --arg status "$status" \
    --argjson active_feature "$active_json" \
    --argjson dirty_tree "$dirty_json" \
    --argjson backup "$backup_json" \
    --argjson items "$items_json" \
    --argjson recovery "$recovery_json" \
    '{
      schema_version: 1,
      script: $script,
      mode: $mode,
      repo_root: $repo_root,
      spec_dir: null,
      active_feature: $active_feature,
      dirty_tree: $dirty_tree,
      backup: $backup,
      status: $status,
      items: $items,
      recovery: $recovery
    }'
  exit "$exit_code"
}

active_json="$(active_feature_json)"
active_state="$(printf '%s' "$active_json" | jq -r '.state')"
active_path="$(printf '%s' "$active_json" | jq -r '.path // ""')"

dirty_entries="$(git -C "$REPO_ROOT" status --porcelain=v1 --untracked-files=all)"
dirty_entries_json="$(printf '%s\n' "$dirty_entries" | json_array_from_lines)"
is_dirty=false
[ -n "$dirty_entries" ] && is_dirty=true

nav_current=false
marker_is_current=false
marker_current && marker_is_current=true
if [ "$marker_is_current" = "true" ] && generator_current; then
  nav_current=true
fi

if [ "$marker_is_current" = "true" ]; then
  add_item "noop_current" ".specify/structure-version.json" "" "" "" 10
else
  add_item "pending" ".specify/structure-version.json" "repo_structure_marker" "" "" 10
fi

rule_count="$(grep -cxF "$PROCESS_RULE" "$REPO_ROOT/.gitattributes" 2>/dev/null || true)"
if [ "$rule_count" = "1" ]; then
  add_item "noop_current" ".gitattributes" "process_linguist_generated_rule" "" "" 10
else
  add_item "pending" ".gitattributes" "process_linguist_generated_rule" "" "" 10
fi

roadmap="$REPO_ROOT/docs/ai/specs/pr-size-governance-technical-roadmap.md"
if [ -f "$roadmap" ] && grep -E 'split exception|transition exception|ratified exception' "$roadmap" >/dev/null 2>&1; then
  add_item "pending" "docs/ai/specs/pr-size-governance-technical-roadmap.md" "roadmap_deboilerplate" "" "" 10
elif [ -f "$roadmap" ]; then
  add_item "noop_current" "docs/ai/specs/pr-size-governance-technical-roadmap.md" "roadmap_deboilerplate" "" "" 10
fi

collect_candidates "$active_path" "$nav_current"
if [ "$nav_current" = "true" ]; then
  add_item "noop_current" "GENERATED:INDEX" "generated_navigation_current" "" "" 30
fi

pending_count="$(jq -cs '[.[] | select(.action == "pending" or .action == "generated_update")] | length' "$ITEMS_FILE")"
dirty_apply_block=false

if [ "$MODE" = "apply" ] && [ "$active_state" = "invalid" ]; then
  dirty_json="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:false}')"
  emit_report "blocked_active_feature_invalid" "$active_json" "$dirty_json" 2
fi

if [ "$pending_count" -eq 0 ]; then
  dirty_json="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:false}')"
  emit_report "noop" "$active_json" "$dirty_json" 0
fi

if [ "$MODE" = "apply" ] && [ "$is_dirty" = "true" ]; then
  dirty_apply_block=true
  dirty_json="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" --argjson apply_blocked "$dirty_apply_block" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:$apply_blocked}')"
  emit_report "blocked_dirty_tree" "$active_json" "$dirty_json" 2
fi

dirty_json="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:false}')"

if [ "$MODE" = "dry-run" ]; then
  emit_report "pending" "$active_json" "$dirty_json" 0
fi

if ! create_backup; then
  add_item "failed_backup" "$backup_path" "" "" "" 5
  emit_report "failed_backup" "$active_json" "$dirty_json" 2
fi
backup_created=true
add_item "backup" "$backup_path" "" "" "" 5

if ! mkdir -p "$REPO_ROOT/.specify"; then
  emit_report "failed_marker_write" "$active_json" "$dirty_json" 2 true "Restore from $backup_path before retrying."
fi
if ! printf '{"structureVersion":1}\n' > "$REPO_ROOT/.specify/structure-version.json"; then
  emit_report "failed_marker_write" "$active_json" "$dirty_json" 2 true "Restore from $backup_path before retrying."
fi

ensure_process_rule
deboilerplate_roadmap

if ! "$GEN" "$REPO_ROOT" >"$TMP_DIR/generator.out" 2>"$TMP_DIR/generator.err"; then
  add_item "failed_generator" "GENERATED:INDEX" "" "" "" 30
  emit_report "failed_generator" "$active_json" "$dirty_json" 2 true "Restore from $backup_path before retrying."
fi

emit_report "applied" "$active_json" "$dirty_json" 0

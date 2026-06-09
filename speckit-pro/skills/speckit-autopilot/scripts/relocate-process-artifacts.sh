#!/usr/bin/env bash
# relocate-process-artifacts.sh - PRSG-011 Tier-2 PROCESS relocation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
GEN="$SCRIPT_DIR/generate-spec-index.sh"

# shellcheck source=lib/moc-id-normalize.sh
source "$SCRIPT_DIR/lib/moc-id-normalize.sh"
# shellcheck source=lib/moc-frontmatter.sh
source "$SCRIPT_DIR/lib/moc-frontmatter.sh"

MODE=""
REPO_ROOT=""
SPEC_ARG=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      [ -z "$MODE" ] || { printf 'relocate-process-artifacts.sh: specify exactly one mode\n' >&2; exit 2; }
      MODE="dry-run"
      ;;
    --apply)
      [ -z "$MODE" ] || { printf 'relocate-process-artifacts.sh: specify exactly one mode\n' >&2; exit 2; }
      MODE="apply"
      ;;
    --repo-root|--spec)
      flag="$1"
      shift
      [ $# -gt 0 ] || { printf 'relocate-process-artifacts.sh: %s requires a value\n' "$flag" >&2; exit 2; }
      if [ "$flag" = "--repo-root" ]; then REPO_ROOT="$1"; else SPEC_ARG="$1"; fi
      ;;
    -h|--help)
      printf 'Usage: relocate-process-artifacts.sh (--dry-run|--apply) --spec <spec-dir> [--repo-root <path>]\n'
      exit 0
      ;;
    *)
      printf 'relocate-process-artifacts.sh: unknown argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
  shift
done

[ -n "$MODE" ] || { printf 'relocate-process-artifacts.sh: specify exactly one mode\n' >&2; exit 2; }
[ -n "$SPEC_ARG" ] || { printf 'relocate-process-artifacts.sh: --spec is required\n' >&2; exit 2; }

if [ -z "$REPO_ROOT" ]; then
  REPO_ROOT="$(cd "$PLUGIN_ROOT/.." && pwd -P)"
else
  REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)" || { printf 'relocate-process-artifacts.sh: invalid repo root\n' >&2; exit 2; }
fi
[ -d "$REPO_ROOT" ] || { printf 'relocate-process-artifacts.sh: repo root is not a directory: %s\n' "$REPO_ROOT" >&2; exit 2; }
git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  printf 'relocate-process-artifacts.sh: repo root is not inside a git worktree: %s\n' "$REPO_ROOT" >&2
  exit 2
}

case "$SPEC_ARG" in
  /*) spec_abs="$SPEC_ARG" ;;
  *) spec_abs="$REPO_ROOT/$SPEC_ARG" ;;
esac
[ -d "$spec_abs" ] || { printf 'relocate-process-artifacts.sh: spec dir is not a directory: %s\n' "$SPEC_ARG" >&2; exit 2; }
spec_abs="$(cd "$spec_abs" && pwd -P)"
case "$spec_abs" in
  "$REPO_ROOT"/*) ;;
  *) printf 'relocate-process-artifacts.sh: spec dir is outside repo root: %s\n' "$SPEC_ARG" >&2; exit 2 ;;
esac
SPEC_REL="${spec_abs#"$REPO_ROOT/"}"
SPEC_BASE="$(basename "$SPEC_REL")"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/relocate-process.XXXXXX")"
trap 'rm -rf "$TMP_DIR"' EXIT
ITEMS_FILE="$TMP_DIR/items.jsonl"
MOVES_FILE="$TMP_DIR/moves.tsv"
: > "$ITEMS_FILE"
: > "$MOVES_FILE"

backup_stamp="${SPECKIT_MIGRATION_BACKUP_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
backup_root="${SPECKIT_MIGRATION_BACKUP_ROOT:-/tmp}"
backup_path="$backup_root/speckit-migration-backup-$backup_stamp"
backup_created=false
collision_count=0

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

add_move() {
  local action="$1" source="$2" target="$3" reason="${4:-}" tier="${5:-30}"
  add_item "$action" "" "$reason" "$target" "$source" "$tier"
  printf '%s\t%s\n' "$source" "$target" >> "$MOVES_FILE"
}

add_collision() {
  local source="$1" target="$2" reason="${3:-target_exists}"
  collision_count=$((collision_count + 1))
  add_item "collision" "" "$reason" "$target" "$source" 25
}

json_array_from_lines() {
  jq -Rsc 'split("\n") | map(select(length > 0))'
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

is_active_spec() {
  local active_path="$1" active_base
  [ -n "$active_path" ] || return 1
  active_base="$(basename "$active_path")"
  [ "$SPEC_REL" = "$active_path" ] && return 0
  moc_id_match "$active_base" "$SPEC_BASE"
}

generator_current() {
  local rc=0
  "$GEN" --check "$REPO_ROOT" >/dev/null 2>"$TMP_DIR/generator-check.err" || rc=$?
  [ "$rc" -eq 0 ]
}

move_target_or_collision() {
  local action="$1" source="$2" target="$3" reason="${4:-}"
  if [ -e "$REPO_ROOT/$target" ]; then
    add_collision "$source" "$target" "target_exists"
  else
    add_move "$action" "$source" "$target" "$reason"
  fi
}

collect_contracts() {
  local rel
  for rel in SPEC-MOC.md spec.md plan.md tasks.md research.md data-model.md quickstart.md; do
    [ -f "$spec_abs/$rel" ] && add_item "protected_contract" "$SPEC_REL/$rel" "" "" "" 10
  done
  if [ -d "$spec_abs/contracts" ]; then
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      add_item "protected_contract" "$SPEC_REL/contracts/$rel" "" "" "" 10
    done < <(cd "$spec_abs/contracts" && find . -type f | sed 's#^\./##' | LC_ALL=C sort)
  fi
  if [ -d "$spec_abs/checklists" ]; then
    while IFS= read -r rel; do
      [ -n "$rel" ] || continue
      add_item "protected_contract" "$SPEC_REL/checklists/$rel" "" "" "" 10
    done < <(cd "$spec_abs/checklists" && find . -type f | sed 's#^\./##' | LC_ALL=C sort)
  fi
}

collect_existing_process_noops() {
  [ -d "$spec_abs/.process" ] || return 0
  local rel
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    add_item "noop_current" "$SPEC_REL/.process/$rel" "" "" "" 15
  done < <(cd "$spec_abs/.process" && find . -type f | sed 's#^\./##' | LC_ALL=C sort)
}

collect_simple_process_moves() {
  local rel target
  for rel in retrospective.md analysis.md cleanup-report.md incident-report.md uat-notes.md design-concept.md workflow.md; do
    [ -f "$spec_abs/$rel" ] || continue
    target="$SPEC_REL/.process/$rel"
    move_target_or_collision "move" "$SPEC_REL/$rel" "$target"
  done
}

collect_review_packet() {
  local sources=()
  local rel target="$SPEC_REL/.process/pr-review-packet.md"
  [ -f "$spec_abs/pr-review-packet.md" ] && sources+=("$SPEC_REL/pr-review-packet.md")
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    sources+=("$SPEC_REL/$rel")
  done < <(cd "$spec_abs" && find . -maxdepth 1 -type f -name 'peer-review-*' | sed 's#^\./##' | LC_ALL=C sort)

  if [ "${#sources[@]}" -eq 0 ]; then
    [ -f "$REPO_ROOT/$target" ] && add_item "noop_current" "$target" "" "" "" 15
    return 0
  fi
  if [ "${#sources[@]}" -gt 1 ] || [ -e "$REPO_ROOT/$target" ]; then
    local source
    for source in "${sources[@]}"; do
      add_collision "$source" "$target" "review_packet_target_collision"
    done
    return 0
  fi
  add_move "move" "${sources[0]}" "$target" "review_packet_canonicalization"
}

collect_evidence() {
  local canonical="$SPEC_REL/.process/evidence/verification-evidence.md"
  local sources=()
  [ -f "$spec_abs/verification-evidence.md" ] && sources+=("$SPEC_REL/verification-evidence.md")
  [ -f "$spec_abs/evidence/verification-evidence.md" ] && sources+=("$SPEC_REL/evidence/verification-evidence.md")

  if [ "${#sources[@]}" -gt 1 ] || { [ "${#sources[@]}" -eq 1 ] && [ -e "$REPO_ROOT/$canonical" ]; }; then
    local source
    for source in "${sources[@]}"; do
      add_collision "$source" "$canonical" "evidence_target_collision"
    done
    return 0
  fi

  if [ "${#sources[@]}" -eq 1 ]; then
    add_move "normalize" "${sources[0]}" "$canonical" "verification_evidence"
  elif [ -f "$REPO_ROOT/$canonical" ]; then
    add_item "noop_current" "$canonical" "" "" "" 15
  fi

  [ -d "$spec_abs/evidence" ] || return 0
  local rel source target
  while IFS= read -r rel; do
    [ -n "$rel" ] || continue
    source="$SPEC_REL/evidence/$rel"
    target="$SPEC_REL/.process/evidence/$rel"
    if [ "$source" = "${sources[0]:-}" ]; then
      continue
    fi
    move_target_or_collision "move" "$source" "$target" "evidence_directory"
  done < <(cd "$spec_abs/evidence" && find . -type f | sed 's#^\./##' | LC_ALL=C sort)
}

collect_docs_side_moves() {
  local docs_dir="$REPO_ROOT/docs/ai/specs"
  [ -d "$docs_dir" ] || return 0
  local name source target
  for name in "$SPEC_BASE-design-concept.md" "$SPEC_BASE-workflow.md"; do
    source="docs/ai/specs/$name"
    target="docs/ai/specs/.process/$name"
    [ -f "$REPO_ROOT/$source" ] || continue
    move_target_or_collision "move" "$source" "$target" "docs_side_process_anchor"
  done
}

stamp_needed() {
  ! moc_is_gated "$spec_abs/SPEC-MOC.md"
}

stamp_moc() {
  local file="$spec_abs/SPEC-MOC.md" tmp="$TMP_DIR/SPEC-MOC.md"
  awk '
    BEGIN { in_fm = 0; done = 0 }
    NR == 1 && $0 == "---" { in_fm = 1; print; next }
    in_fm && $0 ~ /^[[:space:]]*structureVersion:/ {
      if (!done) { print "structureVersion: 1"; done = 1 }
      next
    }
    in_fm && $0 == "---" {
      if (!done) { print "structureVersion: 1"; done = 1 }
      in_fm = 0
      print
      next
    }
    { print }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

move_one() {
  local source="$1" target="$2"
  mkdir -p "$(dirname "$REPO_ROOT/$target")"
  git -C "$REPO_ROOT" mv "$source" "$target" >/dev/null 2>&1 || mv "$REPO_ROOT/$source" "$REPO_ROOT/$target"
}

apply_moves() {
  local source target
  while IFS=$'\t' read -r source target; do
    [ -n "$source" ] || continue
    move_one "$source" "$target"
  done < "$MOVES_FILE"
  [ -d "$spec_abs/evidence" ] && rmdir "$spec_abs/evidence" 2>/dev/null || true
}

create_backup() {
  mkdir -p "$backup_path" || return 1
  [ -e "$REPO_ROOT/docs/ai/specs" ] && mkdir -p "$backup_path/docs/ai" && cp -R "$REPO_ROOT/docs/ai/specs" "$backup_path/docs/ai/specs" 2>/dev/null || true
  [ -e "$REPO_ROOT/$SPEC_REL" ] && mkdir -p "$backup_path/$(dirname "$SPEC_REL")" && cp -R "$REPO_ROOT/$SPEC_REL" "$backup_path/$SPEC_REL" 2>/dev/null || true
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
    --arg script "relocate-process-artifacts" \
    --arg mode "$MODE" \
    --arg repo_root "$REPO_ROOT" \
    --arg spec_dir "$SPEC_REL" \
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
      spec_dir: $spec_dir,
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
dirty_json_clean="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:false}')"

if [ "$MODE" = "apply" ] && [ "$active_state" = "invalid" ]; then
  emit_report "blocked_active_feature_invalid" "$active_json" "$dirty_json_clean" 2
fi

reason="$(out_of_scope_reason "$SPEC_BASE" || true)"
if [ -n "$reason" ]; then
  add_item "skipped_out_of_scope" "$SPEC_REL" "$reason" "" "" 20
  emit_report "noop" "$active_json" "$dirty_json_clean" 0
fi

if is_active_spec "$active_path"; then
  add_item "skipped_frozen_in_flight" "$SPEC_REL" "" "" "" 20
  emit_report "noop" "$active_json" "$dirty_json_clean" 0
fi

moc="$spec_abs/SPEC-MOC.md"
if [ -L "$moc" ] || [ ! -f "$moc" ]; then
  emit_report "blocked_missing_moc" "$active_json" "$dirty_json_clean" 2
fi

collect_contracts
collect_existing_process_noops
collect_simple_process_moves
collect_review_packet
collect_evidence
collect_docs_side_moves

stamp_is_needed=false
if stamp_needed; then
  stamp_is_needed=true
  add_item "stamp" "$SPEC_REL/SPEC-MOC.md" "" "" "" 35
else
  add_item "noop_current" "$SPEC_REL/SPEC-MOC.md" "structureVersion" "" "" 35
fi

move_count="$(wc -l < "$MOVES_FILE" | tr -d ' ')"
gen_current=false
if generator_current; then gen_current=true; fi
if [ "$move_count" -gt 0 ] || [ "$stamp_is_needed" = "true" ] || [ "$gen_current" != "true" ]; then
  add_item "generated_update" "GENERATED:INDEX" "" "" "" 40
else
  add_item "noop_current" "GENERATED:INDEX" "generated_navigation_current" "" "" 40
fi

pending_count="$(jq -cs '[.[] | select(.action == "move" or .action == "normalize" or .action == "stamp" or .action == "generated_update")] | length' "$ITEMS_FILE")"

if [ "$collision_count" -gt 0 ]; then
  if [ "$MODE" = "apply" ]; then
    emit_report "blocked_collision" "$active_json" "$dirty_json_clean" 2
  fi
  emit_report "blocked_collision" "$active_json" "$dirty_json_clean" 0
fi

if [ "$pending_count" -eq 0 ]; then
  emit_report "noop" "$active_json" "$dirty_json_clean" 0
fi

if [ "$MODE" = "apply" ] && [ "$is_dirty" = "true" ]; then
  dirty_json_blocked="$(jq -cn --argjson is_dirty "$is_dirty" --argjson entries "$dirty_entries_json" '{is_dirty:$is_dirty, entries:$entries, apply_blocked:true}')"
  emit_report "blocked_dirty_tree" "$active_json" "$dirty_json_blocked" 2
fi

if [ "$MODE" = "dry-run" ]; then
  emit_report "pending" "$active_json" "$dirty_json_clean" 0
fi

if ! create_backup; then
  add_item "failed_backup" "$backup_path" "" "" "" 5
  emit_report "failed_backup" "$active_json" "$dirty_json_clean" 2
fi
backup_created=true
add_item "backup" "$backup_path" "" "" "" 5

if ! apply_moves; then
  emit_report "failed_move" "$active_json" "$dirty_json_clean" 2 true "Restore from $backup_path before retrying."
fi

if [ "$stamp_is_needed" = "true" ]; then
  if ! stamp_moc; then
    emit_report "failed_stamp" "$active_json" "$dirty_json_clean" 2 true "Restore from $backup_path before retrying."
  fi
fi

if ! "$GEN" "$REPO_ROOT" >"$TMP_DIR/generator.out" 2>"$TMP_DIR/generator.err"; then
  emit_report "failed_generator" "$active_json" "$dirty_json_clean" 2 true "Restore from $backup_path before retrying."
fi

emit_report "applied" "$active_json" "$dirty_json_clean" 0

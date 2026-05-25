#!/usr/bin/env bash
#
# install-curated-set.sh — Install or upgrade speckit-pro's curated set of
# community extensions and presets.
#
# Non-interactive. The slash-command bodies (commands/install.md and
# commands/upgrade.md for Claude Code, codex-skills/speckit-install and
# codex-skills/speckit-upgrade for Codex) handle user prompting and pass
# the resolved selection in via --accept=<csv>.
#
# Resolution: latest GitHub Release tag at invocation time, falling back to
# latest git tag if no Release exists, failing if neither. NEVER falls back
# to main — preserves the pinned-ref discipline documented in
# speckit-pro/skills/speckit-coach/references/presets-extensions-guide.md.

set -euo pipefail

print_usage() {
  cat <<'EOF'
Usage: install-curated-set.sh [OPTIONS]

  --mode=install|upgrade|check    Default: install
  --accept=<csv>                  Comma-separated ids to act on. Empty = all.
  --manifest=<path>               Default: <script-dir>/curated-set.json
  --provenance-log=<path>         Default: .specify/curated-install.json

Environment overrides (for tests): SPECIFY, GH, JQ.

Exit codes:
  0  success (or check mode with no work pending)
  2  check mode: work pending
  1  error
EOF
}

MODE="install"
ACCEPT=""
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
MANIFEST="$SCRIPT_DIR/curated-set.json"
PROVENANCE_LOG=".specify/curated-install.json"
SPECIFY="${SPECIFY:-specify}"
GH="${GH:-gh}"
JQ="${JQ:-jq}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode=*) MODE="${1#*=}";;
    --accept=*) ACCEPT="${1#*=}";;
    --manifest=*) MANIFEST="${1#*=}";;
    --provenance-log=*) PROVENANCE_LOG="${1#*=}";;
    -h|--help) print_usage; exit 0;;
    *) echo "unknown argument: $1" >&2; print_usage >&2; exit 1;;
  esac
  shift
done

case "$MODE" in
  install|upgrade|check) ;;
  *) echo "invalid --mode: $MODE" >&2; exit 1;;
esac

for tool in "$SPECIFY" "$GH" "$JQ"; do
  command -v "$tool" >/dev/null 2>&1 || { echo "$tool not on PATH" >&2; exit 1; }
done
[[ -f "$MANIFEST" ]] || { echo "manifest not found: $MANIFEST" >&2; exit 1; }

# Resolve "$1" (github repo "owner/name") to "<ref_kind>:<ref_tag>" or empty.
# ref_kind ∈ {release, tag}. Failure path is silent — caller decides whether
# to warn or fail.
resolve_ref() {
  local repo="$1"
  local tag
  tag=$("$GH" release list --repo "$repo" --limit 1 --json tagName --jq '.[0].tagName // ""' 2>/dev/null || true)
  if [[ -n "$tag" ]]; then
    printf 'release:%s\n' "$tag"
    return 0
  fi
  tag=$("$GH" api "repos/$repo/tags" --jq '.[0].name // ""' 2>/dev/null || true)
  if [[ -n "$tag" ]]; then
    printf 'tag:%s\n' "$tag"
    return 0
  fi
  return 1
}

# Print the installed version of "$2" (id) for kind "$1" (extension|preset),
# or empty if not installed. Reads .specify/ directly because `specify list`
# has no machine-readable output mode in v0.8.13.
installed_version() {
  local kind="$1" id="$2"
  if [[ "$kind" == "extension" ]]; then
    local registry="${SPECIFY_EXTENSIONS_REGISTRY:-.specify/extensions/.registry}"
    [[ -f "$registry" ]] || { echo ""; return; }
    "$JQ" -r --arg id "$id" '.extensions[$id].version // ""' "$registry" 2>/dev/null || echo ""
  else
    local preset_yml="${SPECIFY_PRESETS_DIR:-.specify/presets}/$id/preset.yml"
    [[ -f "$preset_yml" ]] || { echo ""; return; }
    grep -E '^version:' "$preset_yml" 2>/dev/null | head -1 \
      | sed -E 's/^version:[[:space:]]*//; s/^"//; s/"$//; s/^'\''//; s/'\''$//' \
      || echo ""
  fi
}

# Normalize a tag for equality comparison ("v1.0.0" → "1.0.0").
norm_tag() { echo "${1#v}"; }

declare -a actions_json=()
record_action() {
  local id="$1" action="$2" kind="$3" ref_kind="$4" ref_tag="$5" from_ver="$6" repo="$7" zip_url="$8"
  actions_json+=("$("$JQ" -nc \
    --arg id "$id" --arg action "$action" --arg kind "$kind" \
    --arg ref_kind "$ref_kind" --arg ref_tag "$ref_tag" --arg from_ver "$from_ver" \
    --arg repo "$repo" --arg zip_url "$zip_url" \
    '{id:$id, action:$action, kind:$kind, ref_kind:$ref_kind, ref_tag:$ref_tag, from_version:$from_ver, repo:$repo, zip_url:$zip_url}')")
}

want_id() {
  local id="$1"
  [[ -z "$ACCEPT" ]] && return 0
  [[ ",$ACCEPT," == *",$id,"* ]]
}

entries=$("$JQ" -r '.entries[] | "\(.id)|\(.kind)|\(.repo)"' "$MANIFEST")

while IFS='|' read -r id kind repo; do
  [[ -z "$id" ]] && continue
  want_id "$id" || continue

  ref=$(resolve_ref "$repo" || true)
  if [[ -z "$ref" ]]; then
    echo "[$id] no GitHub Release and no git tag found in $repo — cannot resolve a pinned ref." >&2
    echo "        Open an issue with the extension author asking for a tagged release, or install manually with a SHA pin via the coach playbook." >&2
    continue
  fi
  ref_kind="${ref%%:*}"
  ref_tag="${ref#*:}"
  zip_url="https://github.com/$repo/archive/refs/tags/$ref_tag.zip"

  installed=$(installed_version "$kind" "$id")
  installed_norm=$(norm_tag "$installed")
  ref_norm=$(norm_tag "$ref_tag")

  case "$MODE" in
    install)
      if [[ -n "$installed" ]]; then
        echo "[$id] already installed ($installed) — skipping"
        continue
      fi
      echo "[$id] installing $kind from $ref_kind:$ref_tag"
      "$SPECIFY" "$kind" add --from "$zip_url"
      record_action "$id" "installed" "$kind" "$ref_kind" "$ref_tag" "" "$repo" "$zip_url"
      ;;
    upgrade)
      if [[ -z "$installed" ]]; then
        echo "[$id] missing — installing $kind from $ref_kind:$ref_tag"
        "$SPECIFY" "$kind" add --from "$zip_url"
        record_action "$id" "installed" "$kind" "$ref_kind" "$ref_tag" "" "$repo" "$zip_url"
      elif [[ "$installed_norm" != "$ref_norm" ]]; then
        echo "[$id] upgrading $installed → $ref_tag"
        "$SPECIFY" "$kind" remove "$id" >/dev/null 2>&1 || true
        "$SPECIFY" "$kind" add --from "$zip_url"
        record_action "$id" "upgraded" "$kind" "$ref_kind" "$ref_tag" "$installed" "$repo" "$zip_url"
      else
        echo "[$id] already at latest ($installed) — skipping"
      fi
      ;;
    check)
      if [[ -z "$installed" ]]; then
        echo "[$id] would install $kind at $ref_kind:$ref_tag"
        record_action "$id" "would-install" "$kind" "$ref_kind" "$ref_tag" "" "$repo" "$zip_url"
      elif [[ "$installed_norm" != "$ref_norm" ]]; then
        echo "[$id] would upgrade $installed → $ref_tag"
        record_action "$id" "would-upgrade" "$kind" "$ref_kind" "$ref_tag" "$installed" "$repo" "$zip_url"
      fi
      ;;
  esac
done <<<"$entries"

if [[ "$MODE" != "check" && ${#actions_json[@]} -gt 0 ]]; then
  mkdir -p "$(dirname "$PROVENANCE_LOG")"
  timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  actions_array=$(printf '%s\n' "${actions_json[@]}" | "$JQ" -s '.')
  new_entry=$("$JQ" -n \
    --arg ts "$timestamp" --arg mode "$MODE" --argjson actions "$actions_array" \
    '{timestamp:$ts, mode:$mode, actions:$actions}')
  if [[ -f "$PROVENANCE_LOG" ]]; then
    tmp=$(mktemp)
    "$JQ" --argjson entry "$new_entry" '.history += [$entry]' "$PROVENANCE_LOG" > "$tmp"
    mv "$tmp" "$PROVENANCE_LOG"
  else
    "$JQ" -n --argjson entry "$new_entry" '{history:[$entry]}' > "$PROVENANCE_LOG"
  fi
fi

if [[ "$MODE" == "check" && ${#actions_json[@]} -gt 0 ]]; then
  exit 2
fi
exit 0

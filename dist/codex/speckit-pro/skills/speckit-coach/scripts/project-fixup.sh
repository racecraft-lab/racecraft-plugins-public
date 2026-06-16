#!/usr/bin/env bash
# project-fixup.sh — Audit and repair common SpecKit project drift.
#
# Usage:
#   project-fixup.sh audit [project-root] [preset-id]
#   project-fixup.sh apply [project-root] [preset-id]
#
# The apply mode copies reviewability-related direct core template edits into
# a project-local preset and registers that preset. It does not restore core
# templates, because the safe source of core defaults is project-specific
# version control or a reviewed Spec Kit re-init/upgrade.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../speckit-autopilot/scripts/lib/specify-cli.sh"

MODE="${1:-audit}"
PROJECT_ROOT="${2:-$PWD}"
PRESET_ID="${3:-speckit-pro-reviewability}"

case "$MODE" in
  audit|apply) ;;
  *)
    printf '{"error":"Usage: project-fixup.sh <audit|apply> [project-root] [preset-id]"}\n'
    exit 2
    ;;
esac

if ! PROJECT_ROOT_RESOLVED="$(cd "$PROJECT_ROOT" 2>/dev/null && pwd)"; then
  jq -cn \
    --arg error "project root not accessible" \
    --arg project_root "$PROJECT_ROOT" \
    '{error:$error,project_root:$project_root}'
  exit 2
fi
PROJECT_ROOT="$PROJECT_ROOT_RESOLVED"
SPECIFY_DIR="$PROJECT_ROOT/.specify"
TEMPLATES_DIR="$SPECIFY_DIR/templates"
PRESETS_DIR="$SPECIFY_DIR/presets"
PRESET_DIR="$PRESETS_DIR/$PRESET_ID"
REGISTRY_FILE="$PRESETS_DIR/.registry"

templates=(spec-template plan-template tasks-template)
marker_regex='Reviewability|reviewability budget|PR Review Packet|PR review packet|review packet'

json_array_from_lines() {
  if [ "$#" -eq 0 ]; then
    printf '[]'
  else
    printf '%s\n' "$@" | jq -R . | jq -s .
  fi
}

find_pr_template() {
  local root="$1"
  local candidate
  for candidate in \
    "$root/.github/pull_request_template.md" \
    "$root/.github/PULL_REQUEST_TEMPLATE.md" \
    "$root/docs/pull_request_template.md" \
    "$root/pull_request_template.md"; do
    [ -f "$candidate" ] && printf '%s\n' "$candidate" && return 0
  done

  if [ -d "$root/.github/PULL_REQUEST_TEMPLATE" ]; then
    find "$root/.github/PULL_REQUEST_TEMPLATE" -maxdepth 1 -type f -name '*.md' | sort | head -n 1
  fi
}

resolve_template() {
  local name="$1"
  if speckit_have_specify; then
    (cd "$PROJECT_ROOT" && speckit_specify preset resolve "$name" 2>/dev/null) | tr '\n' ' ' | sed 's/[[:space:]][[:space:]]*/ /g' || true
  fi
}

direct_core=()
template_items=()
for template in "${templates[@]}"; do
  path="$TEMPLATES_DIR/$template.md"
  has_marker=false
  if [ -f "$path" ] && grep -Eiq "$marker_regex" "$path"; then
    has_marker=true
    direct_core+=("$template")
  fi

  resolved="$(resolve_template "$template")"
  item="$(jq -cn \
    --arg name "$template" \
    --arg path "$path" \
    --argjson core_has_reviewability "$has_marker" \
    --arg resolved "$resolved" \
    '{name:$name,path:$path,core_has_reviewability:$core_has_reviewability,resolved:$resolved}')"
  template_items+=("$item")
done

template_json="$(printf '%s\n' "${template_items[@]}" | jq -s '.')"
direct_core_json="$(json_array_from_lines "${direct_core[@]}")"

has_specify_project=false
[ -d "$SPECIFY_DIR" ] && has_specify_project=true

preset_installed=false
[ -f "$PRESET_DIR/preset.yml" ] && preset_installed=true

preset_registered=false
if [ -f "$REGISTRY_FILE" ] && jq -e --arg id "$PRESET_ID" '.presets[$id] // empty' "$REGISTRY_FILE" >/dev/null 2>&1; then
  preset_registered=true
fi

pr_template="$(find_pr_template "$PROJECT_ROOT" || true)"

actions=()
status="pass"
if [ "$has_specify_project" != "true" ]; then
  status="block"
  actions+=("Run from an initialized SpecKit project with a .specify directory.")
elif [ "${#direct_core[@]}" -gt 0 ]; then
  status="warn"
  actions+=("Run apply mode to copy reviewability direct core template edits into .specify/presets/$PRESET_ID/.")
  actions+=("After preset resolution is verified, restore affected .specify/templates/*.md files from version control or reviewed Spec Kit defaults.")
fi

if [ -z "$pr_template" ]; then
  actions+=("Add .github/pull_request_template.md so generated PR review packets preserve host repository requirements.")
fi

if [ "$MODE" = "apply" ]; then
  if [ "$has_specify_project" != "true" ]; then
    printf '{"status":"block","error":"No .specify directory found"}\n'
    exit 1
  fi

  if [ "${#direct_core[@]}" -gt 0 ]; then
    mkdir -p "$PRESET_DIR/templates"

    for template in "${direct_core[@]}"; do
      cp "$TEMPLATES_DIR/$template.md" "$PRESET_DIR/templates/$template.md"
    done

    {
      printf 'schema_version: "1.0"\n\n'
      printf 'preset:\n'
      printf '  id: "%s"\n' "$PRESET_ID"
      printf '  name: "SpecKit Pro Reviewability"\n'
      printf '  version: "1.0.0"\n'
      printf '  description: "Preserves reviewability template requirements outside Spec Kit core templates."\n'
      printf '  author: "speckit-pro"\n\n'
      printf 'requires:\n'
      printf '  speckit_version: ">=0.5.1"\n\n'
      printf 'provides:\n'
      printf '  templates:\n'
      for template in "${direct_core[@]}"; do
        printf '    - type: "template"\n'
        printf '      name: "%s"\n' "$template"
        printf '      file: "templates/%s.md"\n' "$template"
        printf '      description: "Upgrade-safe %s override copied from project template customizations."\n' "$template"
        printf '      replaces: "%s"\n' "$template"
      done
      printf '\ntags:\n'
      printf '  - "reviewability"\n'
      printf '  - "verification-debt"\n'
    } > "$PRESET_DIR/preset.yml"

    mkdir -p "$PRESETS_DIR"
    REGISTRY_FILE="$REGISTRY_FILE" PRESET_ID="$PRESET_ID" python3 - <<'PY'
import json
import os
from pathlib import Path

registry_path = Path(os.environ["REGISTRY_FILE"])
preset_id = os.environ["PRESET_ID"]

if registry_path.exists():
    try:
        data = json.loads(registry_path.read_text())
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

data.setdefault("schema_version", "1.0")
presets = data.setdefault("presets", {})
entry = presets.setdefault(preset_id, {})
entry.update({
    "version": "1.0.0",
    "source": "project-local",
    "manifest_hash": "project-local",
    "enabled": True,
    "priority": min(int(entry.get("priority", 5)), 5),
    "installed_at": "generated-by-speckit-pro-project-fixup",
})

registry_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
PY

    preset_installed=true
    preset_registered=true
    actions+=("Verify with specify preset resolve spec-template/plan-template/tasks-template.")
  fi
fi

actions_json="$(json_array_from_lines "${actions[@]}")"

jq -cn \
  --arg mode "$MODE" \
  --arg project_root "$PROJECT_ROOT" \
  --arg preset_id "$PRESET_ID" \
  --argjson has_specify_project "$has_specify_project" \
  --argjson direct_core_edits "$([ "${#direct_core[@]}" -gt 0 ] && printf true || printf false)" \
  --argjson core_templates_with_reviewability "$direct_core_json" \
  --argjson templates "$template_json" \
  --argjson preset_installed "$preset_installed" \
  --argjson preset_registered "$preset_registered" \
  --arg pr_template "$pr_template" \
  --argjson recommended_actions "$actions_json" \
  --arg status "$status" \
  '{
    mode: $mode,
    project_root: $project_root,
    status: $status,
    preset_id: $preset_id,
    has_specify_project: $has_specify_project,
    direct_core_edits: $direct_core_edits,
    core_templates_with_reviewability: $core_templates_with_reviewability,
    templates: $templates,
    preset_installed: $preset_installed,
    preset_registered: $preset_registered,
    host_pr_template: (if $pr_template == "" then null else $pr_template end),
    recommended_actions: $recommended_actions
  }'

if [ "$status" = "block" ]; then
  exit 1
fi

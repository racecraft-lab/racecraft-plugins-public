#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
SOURCE_DIR="$PLUGIN_ROOT/codex-agents"
DEST_DIR="${1:-${CODEX_AGENTS_DEST:-$HOME/.codex/agents}}"

EXPECTED_AGENTS=(
  phase-executor.toml
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

if [ ! -d "$SOURCE_DIR" ]; then
  printf 'ERROR: source directory not found: %s\n' "$SOURCE_DIR" >&2
  exit 1
fi

missing=()
for agent in "${EXPECTED_AGENTS[@]}"; do
  if [ ! -f "$SOURCE_DIR/$agent" ]; then
    missing+=("$agent")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  printf 'ERROR: missing bundled agent templates in %s\n' "$SOURCE_DIR" >&2
  for agent in "${missing[@]}"; do
    printf '  - %s\n' "$agent" >&2
  done
  exit 1
fi

mkdir -p "$DEST_DIR"

for agent in "${EXPECTED_AGENTS[@]}"; do
  cp -f "$SOURCE_DIR/$agent" "$DEST_DIR/$agent"
done

printf 'Installed %d SpecKit Pro Codex subagents.\n' "${#EXPECTED_AGENTS[@]}"
printf 'Source: %s\n' "$SOURCE_DIR"
printf 'Destination: %s\n' "$DEST_DIR"
printf 'Files:\n'
for agent in "${EXPECTED_AGENTS[@]}"; do
  printf '  - %s\n' "$agent"
done
printf 'Restart Codex now so the custom subagents reload.\n'

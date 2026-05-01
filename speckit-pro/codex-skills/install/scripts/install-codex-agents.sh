#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_ROOT="$(cd "$SKILL_DIR/../.." && pwd)"
SOURCE_DIR="$PLUGIN_ROOT/codex-agents"
DEST_DIR="${CODEX_AGENTS_DEST:-$HOME/.codex/agents}"
TARGET_MODEL="${SPECKIT_CODEX_MODEL:-gpt-5.5}"

EXPECTED_AGENTS=(
  autopilot-fast-helper.toml
  phase-executor.toml
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

GPT55_AGENTS=(
  phase-executor.toml
  clarify-executor.toml
  checklist-executor.toml
  analyze-executor.toml
  implement-executor.toml
  codebase-analyst.toml
  spec-context-analyst.toml
  domain-researcher.toml
)

while [ "$#" -gt 0 ]; do
  case "$1" in
    --model)
      if [ "$#" -lt 2 ]; then
        printf 'ERROR: --model requires a value\n' >&2
        exit 2
      fi
      TARGET_MODEL="$2"
      shift 2
      ;;
    --model=*)
      TARGET_MODEL="${1#--model=}"
      shift
      ;;
    -*)
      printf 'ERROR: unknown option: %s\n' "$1" >&2
      exit 2
      ;;
    *)
      DEST_DIR="$1"
      shift
      ;;
  esac
done

case "$TARGET_MODEL" in
  gpt-5.5|gpt-5.4) ;;
  *)
    printf 'ERROR: unsupported SpecKit Codex model: %s\n' "$TARGET_MODEL" >&2
    printf 'Supported values: gpt-5.5, gpt-5.4\n' >&2
    exit 2
    ;;
esac

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

if [ "$TARGET_MODEL" != "gpt-5.5" ]; then
  for agent in "${GPT55_AGENTS[@]}"; do
    perl -0pi -e 's/^model = "gpt-5\.5"$/model = "'"$TARGET_MODEL"'"/m' "$DEST_DIR/$agent"
  done
fi

printf 'Installed %d SpecKit Pro Codex subagents.\n' "${#EXPECTED_AGENTS[@]}"
printf 'Source: %s\n' "$SOURCE_DIR"
printf 'Destination: %s\n' "$DEST_DIR"
printf 'Executor/consensus model: %s\n' "$TARGET_MODEL"
printf 'Files:\n'
for agent in "${EXPECTED_AGENTS[@]}"; do
  printf '  - %s\n' "$agent"
done
printf 'Model policy: %s for every executor and consensus agent (phase-executor included); Spark helper optional on gpt-5.3-codex-spark.\n' "$TARGET_MODEL"
if [ "$TARGET_MODEL" = "gpt-5.4" ]; then
  printf 'Fallback mode: installed templates were rewritten for GPT-5.4 compatibility.\n'
fi
printf 'Restart Codex now so the custom subagents reload.\n'

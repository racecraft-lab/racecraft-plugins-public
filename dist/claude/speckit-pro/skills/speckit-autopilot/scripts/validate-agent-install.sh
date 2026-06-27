#!/usr/bin/env bash
# validate-agent-install.sh - Verify SpecKit Pro bundled agents are complete.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

SURFACE=""
PLUGIN_ROOT="$DEFAULT_PLUGIN_ROOT"
DEST_DIR=""
AUTOHEAL=0

CODEX_AGENTS=(
  analyze-executor.toml
  autopilot-fast-helper.toml
  checklist-executor.toml
  clarify-executor.toml
  codebase-analyst.toml
  domain-researcher.toml
  implement-executor.toml
  phase-executor.toml
  spec-context-analyst.toml
  uat-runbook-author.toml
)

CLAUDE_AGENTS=(
  analyze-executor.md
  checklist-executor.md
  clarify-executor.md
  codebase-analyst.md
  consensus-synthesizer.md
  domain-researcher.md
  gate-validator.md
  implement-executor.md
  phase-executor.md
  spec-context-analyst.md
  uat-runbook-author.md
)

usage() {
  printf 'Usage: validate-agent-install.sh --surface codex|claude [--plugin-root <path>] [--dest <path>] [--autoheal]\n' >&2
}

fail() {
  local rule="$1" message="$2"
  printf 'validate-agent-install.sh: validation_failure: %s: %s\n' "$rule" "$message" >&2
  exit 1
}

input_error() {
  local message="$1"
  printf 'validate-agent-install.sh: input_error: %s\n' "$message" >&2
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --surface)
      [ "$#" -ge 2 ] || input_error "--surface requires a value"
      SURFACE="$2"
      shift 2
      ;;
    --surface=*)
      SURFACE="${1#--surface=}"
      shift
      ;;
    --plugin-root)
      [ "$#" -ge 2 ] || input_error "--plugin-root requires a value"
      PLUGIN_ROOT="$2"
      shift 2
      ;;
    --plugin-root=*)
      PLUGIN_ROOT="${1#--plugin-root=}"
      shift
      ;;
    --dest)
      [ "$#" -ge 2 ] || input_error "--dest requires a value"
      DEST_DIR="$2"
      shift 2
      ;;
    --dest=*)
      DEST_DIR="${1#--dest=}"
      shift
      ;;
    --autoheal)
      AUTOHEAL=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[ -n "$SURFACE" ] || input_error "--surface is required"
case "$SURFACE" in
  codex|claude) ;;
  *) input_error "unsupported surface: $SURFACE" ;;
esac

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

has_name() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

validate_source_dir() {
  local source_dir="$1" suffix="$2"
  shift 2
  local expected=("$@")
  local missing=() actual=() unexpected=() agent file

  [ -d "$source_dir" ] || input_error "bundled agent source directory not found: $source_dir"

  for agent in "${expected[@]}"; do
    [ -f "$source_dir/$agent" ] || missing+=("$agent")
  done

  while IFS= read -r file; do
    actual+=("$(basename "$file")")
  done < <(find "$source_dir" -maxdepth 1 -type f -name "*.$suffix" -print | sort)

  for agent in "${actual[@]}"; do
    has_name "$agent" "${expected[@]}" || unexpected+=("$agent")
  done

  if [ "${#missing[@]}" -gt 0 ]; then
    printf 'validate-agent-install.sh: missing bundled %s agents in %s\n' "$SURFACE" "$source_dir" >&2
    for agent in "${missing[@]}"; do printf '  - %s\n' "$agent" >&2; done
    exit 1
  fi

  if [ "${#unexpected[@]}" -gt 0 ]; then
    printf 'validate-agent-install.sh: unexpected bundled %s agents in %s; update the install contract\n' "$SURFACE" "$source_dir" >&2
    for agent in "${unexpected[@]}"; do printf '  - %s\n' "$agent" >&2; done
    exit 1
  fi
}

validate_codex_runtime() {
  local source_dir="$PLUGIN_ROOT/codex-agents"
  local destinations=() missing=() agent dest

  validate_source_dir "$source_dir" "toml" "${CODEX_AGENTS[@]}"

  if [ -n "$DEST_DIR" ]; then
    destinations+=("$DEST_DIR")
  else
    destinations+=("$repo_root/.codex/agents")
    destinations+=("$HOME/.codex/agents")
  fi

  for agent in "${CODEX_AGENTS[@]}"; do
    found=0
    for dest in "${destinations[@]}"; do
      if [ -f "$dest/$agent" ]; then
        found=1
        break
      fi
    done
    [ "$found" -eq 1 ] || missing+=("$agent")
  done

  if [ "${#missing[@]}" -gt 0 ] && [ "$AUTOHEAL" -eq 1 ]; then
    local installer heal_dest
    installer="$PLUGIN_ROOT/codex-skills/install/scripts/install-codex-agents.sh"
    [ -x "$installer" ] || input_error "Codex installer not executable: $installer"
    if [ -n "$DEST_DIR" ]; then
      heal_dest="$DEST_DIR"
    else
      heal_dest="$HOME/.codex/agents"
    fi
    "$installer" "$heal_dest" >/dev/null
    missing=()
    for agent in "${CODEX_AGENTS[@]}"; do
      found=0
      for dest in "${destinations[@]}"; do
        if [ -f "$dest/$agent" ]; then
          found=1
          break
        fi
      done
      [ "$found" -eq 1 ] || missing+=("$agent")
    done
  fi

  if [ "${#missing[@]}" -gt 0 ]; then
    printf 'validate-agent-install.sh: missing installed Codex agents\n' >&2
    for agent in "${missing[@]}"; do printf '  - %s\n' "$agent" >&2; done
    fail "codex_agents.incomplete" "run \$install or rerun this check with --autoheal, then restart Codex"
  fi

  printf 'validate-agent-install.sh: ok: codex: %d bundled agents installed\n' "${#CODEX_AGENTS[@]}"
}

validate_claude_runtime() {
  local source_dir="$PLUGIN_ROOT/agents"
  validate_source_dir "$source_dir" "md" "${CLAUDE_AGENTS[@]}"
  printf 'validate-agent-install.sh: ok: claude: %d bundled agents present in plugin package\n' "${#CLAUDE_AGENTS[@]}"
}

case "$SURFACE" in
  codex) validate_codex_runtime ;;
  claude)
    if [ "$AUTOHEAL" -eq 1 ]; then
      printf 'validate-agent-install.sh: note: Claude Code agents load from the plugin package; autoheal is not supported, verifying package completeness only\n' >&2
    fi
    validate_claude_runtime
    ;;
esac

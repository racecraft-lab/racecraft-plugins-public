#!/usr/bin/env bash
# resolve-confidence-mode.sh — Resolve the pre-Implement confidence gate
# mode (advisory or strict) for a given autopilot invocation.
#
# Precedence (highest wins):
#   1. Per-invocation flag: --strict or --advisory in the args
#   2. Local config: `confidence_gate_mode: advisory|strict` in
#      `.claude/speckit-pro.local.md` (or any path passed via --config)
#   3. Default: advisory
#
# Usage:
#   resolve-confidence-mode.sh [--config <path>] [--] <autopilot-args...>
#
# Output:
#   The resolved mode (`advisory` or `strict`) on stdout, one line.
#
# Exit:
#   0 — resolved cleanly
#   1 — usage error (e.g., --config without a path)
#   2 — flag conflict (both --strict and --advisory in args)

set -euo pipefail

CONFIG_PATH=""
# Default search order when --config is not passed: prefer .claude/ first
# (the original CC location), fall back to .codex/ for Codex-only installs.
DEFAULT_CONFIG_CANDIDATES=(
  ".claude/speckit-pro.local.md"
  ".codex/speckit-pro.local.md"
)
ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --config)
      [ -n "${2:-}" ] || { printf 'error: --config requires a path\n' >&2; exit 1; }
      CONFIG_PATH="$2"
      shift 2
      ;;
    --config=*)
      CONFIG_PATH="${1#*=}"
      shift
      ;;
    --)
      shift
      while [ $# -gt 0 ]; do ARGS+=("$1"); shift; done
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

# Scan the args for --strict / --advisory.
seen_strict=0
seen_advisory=0
for arg in "${ARGS[@]:-}"; do
  case "$arg" in
    --strict)    seen_strict=1 ;;
    --advisory)  seen_advisory=1 ;;
  esac
done

if [ "$seen_strict" -eq 1 ] && [ "$seen_advisory" -eq 1 ]; then
  printf 'error: --strict and --advisory are mutually exclusive\n' >&2
  exit 2
fi

if [ "$seen_strict" -eq 1 ]; then
  printf 'strict\n'
  exit 0
fi

if [ "$seen_advisory" -eq 1 ]; then
  printf 'advisory\n'
  exit 0
fi

# No per-invocation flag → read the local config if present.
# If --config was passed, use ONLY that path. Otherwise, search the
# default candidates in priority order (first hit wins).
read_mode_from() {
  local file="$1" mode=""
  [ -f "$file" ] || return 1
  mode="$(
    grep -E '^[[:space:]]*confidence_gate_mode:[[:space:]]*(advisory|strict)[[:space:]]*$' "$file" 2>/dev/null \
      | tail -1 \
      | sed -E 's/^[[:space:]]*confidence_gate_mode:[[:space:]]*(advisory|strict)[[:space:]]*$/\1/' \
      || true
  )"
  if [ "$mode" = "advisory" ] || [ "$mode" = "strict" ]; then
    printf '%s\n' "$mode"
    return 0
  fi
  return 1
}

if [ -n "$CONFIG_PATH" ]; then
  if read_mode_from "$CONFIG_PATH"; then exit 0; fi
else
  for candidate in "${DEFAULT_CONFIG_CANDIDATES[@]}"; do
    if read_mode_from "$candidate"; then exit 0; fi
  done
fi

# Default.
printf 'advisory\n'
exit 0

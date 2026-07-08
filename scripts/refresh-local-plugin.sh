#!/usr/bin/env bash
# refresh-local-plugin.sh -- Maintainer helper for local plugin payload refresh.
#
# Default: rebuild and validate generated payloads, then refresh both the Claude
# Code and Codex installed-plugin caches so local dogfooding picks up changes.
# Opt out of either cache refresh with --no-codex or --no-claude-install.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PLUGIN_NAME="${SPECKIT_PLUGIN_NAME:-speckit-pro}"
MARKETPLACE="${SPECKIT_MARKETPLACE:-racecraft-plugins-public}"
CLAUDE_SCOPE="user"

RUN_BUILD=1
RUN_VALIDATE=1
RUN_CODEX=1
RUN_CLAUDE_INSTALL=1
RUN_CLAUDE_LAUNCH=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage: scripts/refresh-local-plugin.sh [options]

Rebuild generated plugin payloads and refresh the local Claude Code and Codex
installed-plugin caches for maintainer dogfooding.

Default:
  Rebuild dist payloads, validate the Claude payload, refresh both the Claude
  Code and Codex installed-plugin caches, and print the recommended Claude Code
  local-development command:

    claude --plugin-dir dist/claude/speckit-pro

Options:
  --all                Refresh Codex and Claude installed-plugin caches (default).
  --codex              Refresh the Codex installed plugin via remove/add (default).
  --claude-install     Refresh Claude Code's installed plugin cache (default).
  --no-codex           Skip the Codex installed-plugin cache refresh.
  --no-claude-install  Skip Claude Code's installed-plugin cache refresh.
  --launch-claude      Launch Claude Code with --plugin-dir for this session.
  --scope SCOPE        Claude install scope: user, project, or local. Default: user.
  --no-build           Skip payload rebuild.
  --no-validate        Skip Claude payload validation.
  --dry-run            Print commands without running them.
  -h, --help           Show this help.

Environment:
  SPECKIT_PLUGIN_NAME   Plugin name. Default: speckit-pro
  SPECKIT_MARKETPLACE   Marketplace name. Default: racecraft-plugins-public
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

usage_error() {
  echo "error: $*" >&2
  echo >&2
  usage >&2
  exit 2
}

quote_args() {
  local arg
  for arg in "$@"; do
    printf ' %q' "$arg"
  done
}

run_cmd() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+'
    quote_args "$@"
    printf '\n'
  else
    "$@"
  fi
}

run_in_repo() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ cd %q &&' "$REPO_ROOT"
    quote_args "$@"
    printf '\n'
  else
    (cd "$REPO_ROOT" && "$@")
  fi
}

require_cmd() {
  if [ "$DRY_RUN" -eq 1 ]; then
    return
  fi

  if ! command -v "$1" >/dev/null 2>&1; then
    die "required command not found: $1"
  fi
}

plugin_selector() {
  printf '%s@%s' "$PLUGIN_NAME" "$MARKETPLACE"
}

claude_payload_dir() {
  printf '%s/dist/claude/%s' "$REPO_ROOT" "$PLUGIN_NAME"
}

codex_payload_dir() {
  printf '%s/dist/codex/%s' "$REPO_ROOT" "$PLUGIN_NAME"
}

claude_dev_command() {
  printf 'claude --plugin-dir %q\n' "$(claude_payload_dir)"
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --all)
        RUN_CODEX=1
        RUN_CLAUDE_INSTALL=1
        ;;
      --codex)
        RUN_CODEX=1
        ;;
      --claude-install)
        RUN_CLAUDE_INSTALL=1
        ;;
      --no-codex)
        RUN_CODEX=0
        ;;
      --no-claude-install)
        RUN_CLAUDE_INSTALL=0
        ;;
      --launch-claude)
        RUN_CLAUDE_LAUNCH=1
        ;;
      --scope)
        [ "$#" -ge 2 ] || usage_error "--scope requires a value"
        CLAUDE_SCOPE="$2"
        shift
        ;;
      --scope=*)
        CLAUDE_SCOPE="${1#--scope=}"
        ;;
      --no-build)
        RUN_BUILD=0
        ;;
      --no-validate)
        RUN_VALIDATE=0
        ;;
      --dry-run)
        DRY_RUN=1
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        usage_error "unknown option: $1"
        ;;
    esac
    shift
  done

  case "$CLAUDE_SCOPE" in
    user|project|local) ;;
    *) usage_error "--scope must be one of: user, project, local" ;;
  esac
}

validate_layout() {
  [ -f "$REPO_ROOT/scripts/build-plugin-payloads.py" ] || \
    die "payload builder not found: $REPO_ROOT/scripts/build-plugin-payloads.py"

  # Only require pre-existing payloads when we skip the build AND actually run.
  # In --dry-run we just print commands, so missing payloads must not abort.
  if [ "$RUN_BUILD" -eq 0 ] && [ "$DRY_RUN" -eq 0 ]; then
    [ -d "$(claude_payload_dir)" ] || die "Claude payload not found: $(claude_payload_dir)"
    [ -d "$(codex_payload_dir)" ] || die "Codex payload not found: $(codex_payload_dir)"
  fi
}

build_payloads() {
  echo "==> Building generated Claude and Codex payloads ..."
  run_in_repo python3 scripts/build-plugin-payloads.py
}

validate_claude_payload() {
  # Validation is Claude-specific. If the Claude CLI is absent, skip it with a
  # warning rather than aborting a run that may only target Codex. A run that
  # actually needs Claude (install/launch) still fails later via require_cmd.
  # In --dry-run we print the command without requiring the CLI.
  if [ "$DRY_RUN" -eq 0 ] && ! command -v claude >/dev/null 2>&1; then
    echo "warning: 'claude' not found; skipping Claude payload validation (pass --no-validate to silence)." >&2
    return
  fi
  echo "==> Validating Claude Code payload ..."
  run_cmd claude plugin validate "$(claude_payload_dir)"
}

# Prints the local Directory root for $MARKETPLACE (empty when the marketplace
# is absent). Exit status distinguishes the cases the caller must handle:
#   0 = absent, or present as a local Directory (root printed)
#   2 = present but NOT a local Directory source (e.g. a GitHub source)
#   1 = could not list the marketplaces
# The listing is captured first rather than piped into awk, so an early awk
# exit cannot SIGPIPE the CLI into a false failure under `set -o pipefail`.
claude_marketplace_root() {
  local listing
  listing="$(claude plugin marketplace list)" || return 1
  awk -v name="$MARKETPLACE" '
    # Strip the leading selection marker (ASCII ">" or unicode "❯") and
    # surrounding whitespace, then compare the row to the marketplace name as a
    # literal string. A literal compare (not a regex match on $MARKETPLACE)
    # avoids treating regex metacharacters in the name as pattern syntax.
    { row = $0; sub(/^[^[:alnum:]]*/, "", row); sub(/[[:space:]]*$/, "", row) }
    row == name { found = 1; next }
    found == 1 && /^[[:space:]]*Source: Directory \(/ {
      sub(/^[[:space:]]*Source: Directory \(/, "")
      sub(/\)[[:space:]]*$/, "")
      print
      found = 2
      exit 0
    }
    found == 1 && /^[[:space:]]*Source:/ { found = 2; exit 2 }
    END { if (found == 1) exit 2 }
  ' <<<"$listing"
}

ensure_claude_marketplace_is_local() {
  local root rc

  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ claude plugin marketplace list # verify %s points at %q\n' "$MARKETPLACE" "$REPO_ROOT"
    return
  fi

  rc=0
  root="$(claude_marketplace_root)" || rc=$?
  case "$rc" in
    0) ;;
    2) die "Claude marketplace '$MARKETPLACE' exists but is not a local Directory source. Remove it (claude plugin marketplace remove '$MARKETPLACE') before refreshing." ;;
    *) die "failed to inspect Claude marketplace list" ;;
  esac

  if [ "$root" = "$REPO_ROOT" ]; then
    return
  fi

  if [ -n "$root" ]; then
    die "Claude marketplace '$MARKETPLACE' points at '$root', expected '$REPO_ROOT'. Remove or update it explicitly before refreshing."
  fi

  echo "==> Adding Claude marketplace $MARKETPLACE from $REPO_ROOT ..."
  run_cmd claude plugin marketplace add "$REPO_ROOT" --scope "$CLAUDE_SCOPE"
}

refresh_claude_install() {
  require_cmd claude
  ensure_claude_marketplace_is_local

  echo "==> Refreshing $(plugin_selector) in Claude Code ($CLAUDE_SCOPE scope) ..."
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ claude plugin uninstall %q --scope %q -y\n' "$(plugin_selector)" "$CLAUDE_SCOPE"
  else
    local uninstall_output
    if ! uninstall_output="$(claude plugin uninstall "$(plugin_selector)" --scope "$CLAUDE_SCOPE" -y 2>&1)"; then
      case "$uninstall_output" in
        *"not installed"*|*"not found"*) ;;
        *)
          printf '%s\n' "$uninstall_output" >&2
          die "failed to uninstall $(plugin_selector) from Claude Code"
          ;;
      esac
    fi
  fi
  run_cmd claude plugin install "$(plugin_selector)" --scope "$CLAUDE_SCOPE"
  echo "    Restart Claude Code or run /reload-plugins in an existing session."
}

# Prints the marketplace root for $MARKETPLACE (empty when absent); exits 1 if
# the listing could not be obtained. Captured first to avoid a SIGPIPE-induced
# false failure under `set -o pipefail` when awk exits early.
codex_marketplace_root() {
  local listing
  listing="$(codex plugin marketplace list)" || return 1
  awk -v name="$MARKETPLACE" '
    $1 == name {
      root = $0
      sub(/^[[:space:]]*[^[:space:]]+[[:space:]]+/, "", root)
      print root
      exit
    }
  ' <<<"$listing"
}

ensure_codex_marketplace_is_local() {
  local root

  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ codex plugin marketplace list # verify %s points at %q\n' "$MARKETPLACE" "$REPO_ROOT"
    return
  fi

  if ! root="$(codex_marketplace_root)"; then
    die "failed to inspect Codex marketplace list"
  fi

  if [ "$root" = "$REPO_ROOT" ]; then
    return
  fi

  if [ -n "$root" ]; then
    die "Codex marketplace '$MARKETPLACE' points at '$root', expected '$REPO_ROOT'. Remove or update it explicitly before refreshing."
  fi

  echo "==> Adding Codex marketplace $MARKETPLACE from $REPO_ROOT ..."
  run_cmd codex plugin marketplace add "$REPO_ROOT"
}

refresh_codex_install() {
  require_cmd codex
  ensure_codex_marketplace_is_local

  echo "==> Refreshing $(plugin_selector) in Codex ..."
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+ codex plugin remove %q\n' "$(plugin_selector)"
  else
    local remove_output
    if ! remove_output="$(codex plugin remove "$(plugin_selector)" 2>&1)"; then
      case "$remove_output" in
        *"not installed"*|*"not found"*) ;;
        *)
          printf '%s\n' "$remove_output" >&2
          die "failed to remove $(plugin_selector) from Codex"
          ;;
      esac
    fi
  fi
  run_cmd codex plugin add "$(plugin_selector)"
  echo "    Start a new Codex thread to pick up refreshed plugin skills and tools."
}

launch_claude_with_local_payload() {
  require_cmd claude
  echo "==> Launching Claude Code with local payload override ..."
  run_cmd claude --plugin-dir "$(claude_payload_dir)"
}

print_guidance() {
  if [ "$RUN_CLAUDE_LAUNCH" -eq 0 ]; then
    echo
    echo "Claude Code local-development command:"
    printf '  %s\n' "$(claude_dev_command)"
  fi

  if [ "$RUN_CLAUDE_INSTALL" -eq 0 ]; then
    echo "Skipped Claude installed-cache refresh (--no-claude-install)."
  fi

  if [ "$RUN_CODEX" -eq 0 ]; then
    echo "Skipped Codex installed-cache refresh (--no-codex)."
  fi
}

main() {
  parse_args "$@"
  validate_layout

  if [ "$RUN_BUILD" -eq 1 ]; then
    build_payloads
  fi

  if [ "$RUN_VALIDATE" -eq 1 ]; then
    validate_claude_payload
  fi

  if [ "$RUN_CODEX" -eq 1 ]; then
    refresh_codex_install
  fi

  if [ "$RUN_CLAUDE_INSTALL" -eq 1 ]; then
    refresh_claude_install
  fi

  if [ "$RUN_CLAUDE_LAUNCH" -eq 1 ]; then
    launch_claude_with_local_payload
  fi

  print_guidance
}

main "$@"

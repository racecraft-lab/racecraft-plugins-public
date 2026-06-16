# Shared Specify CLI discovery helpers for plugin scripts.

speckit_prepend_cli_paths() {
  local candidate
  for candidate in \
    "${HOME:-}/.local/bin" \
    "/opt/homebrew/bin" \
    "/usr/local/bin"; do
    [ -n "$candidate" ] || continue
    [ -d "$candidate" ] || continue
    case ":${PATH:-}:" in
      *":$candidate:"*) ;;
      *) PATH="$candidate:${PATH:-}" ;;
    esac
  done
  export PATH
}

speckit_find_specify() {
  speckit_prepend_cli_paths
  command -v specify
}

speckit_have_specify() {
  speckit_find_specify >/dev/null 2>&1
}

speckit_specify() {
  local specify_bin
  specify_bin="$(speckit_find_specify 2>/dev/null)" || return 127
  "$specify_bin" "$@"
}

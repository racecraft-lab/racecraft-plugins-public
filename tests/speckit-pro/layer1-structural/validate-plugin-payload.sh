#!/usr/bin/env bash
# validate-plugin-payload.sh — Guard: developer-only content must NOT ship inside the plugin.
#
# Both the Claude Code and Codex marketplaces copy the plugin directory
# (speckit-pro/) verbatim into every consumer's install — neither supports a
# file-exclusion mechanism, so anything under speckit-pro/ ships. The test suite,
# spec artifacts, and process scaffolding are developer-only and intentionally
# live OUTSIDE the plugin (the suite at repo-root tests/speckit-pro/; specs/ and
# .process/ at the repo root). This guard fails if any of them reappear under the
# plugin directory, which would bloat the install and leak internal material to
# consumers.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"

section "plugin payload — developer-only content must not ship in the plugin dir"

# Directories that must never live under the shipped plugin directory.
for forbidden in tests specs .process; do
  set_test "plugin dir does not contain $forbidden/"
  if [ -e "$PLUGIN_ROOT/$forbidden" ]; then
    _fail "$forbidden/ exists under the plugin dir ($PLUGIN_ROOT/$forbidden) — it would ship to consumers. Keep it outside speckit-pro/."
  else
    _pass
  fi
done

test_summary

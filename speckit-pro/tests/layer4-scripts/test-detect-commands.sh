#!/usr/bin/env bash
# test-detect-commands.sh — Unit tests for detect-commands.sh
#
# Tests command detection for Node.js/pnpm, Node.js/npm, Rust, Go,
# Python, Makefile, empty directory, and full verify chain.
# Optional --live flag runs against omnifocus-mcp project.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$PLUGIN_ROOT/skills/speckit-autopilot/scripts/detect-commands.sh"
LIVE=false
[ "${1:-}" = "--live" ] && LIVE=true

FIXTURE_DIR=$(mktemp -d)
trap 'rm -rf "$FIXTURE_DIR"' EXIT

# Helper: run script in a specific directory
run_in() {
  local dir="$1"
  (cd "$dir" && bash "$SCRIPT")
}

# ─────────────────────────────────────────
section "Node.js Projects"
# ─────────────────────────────────────────

set_test "Node.js with pnpm — stack=nodejs"
dir="$FIXTURE_DIR/node-pnpm"
mkdir -p "$dir"
touch "$dir/pnpm-lock.yaml"
cat > "$dir/package.json" << 'PKGJSON'
{
  "scripts": {
    "build": "tsup",
    "typecheck": "tsc --noEmit",
    "lint": "biome check",
    "lint:fix": "biome check --fix",
    "test": "vitest run",
    "test:integration": "vitest run --config vitest.integration.config.ts"
  }
}
PKGJSON
output=$(run_in "$dir")
assert_json_field "$output" "stack" "nodejs"

set_test "Node.js with pnpm — package_manager=pnpm"
assert_json_field "$output" "package_manager" "pnpm"

set_test "Node.js with pnpm — BUILD=pnpm build"
assert_json_field "$output" "commands.BUILD" "pnpm build"

set_test "Node.js with pnpm — TYPECHECK=pnpm typecheck"
assert_json_field "$output" "commands.TYPECHECK" "pnpm typecheck"

set_test "Node.js with pnpm — UNIT_TEST=pnpm test"
assert_json_field "$output" "commands.UNIT_TEST" "pnpm test"

set_test "Node.js with pnpm — INTEGRATION_TEST=pnpm test:integration"
assert_json_field "$output" "commands.INTEGRATION_TEST" "pnpm test:integration"

set_test "Node.js with pnpm — LINT=pnpm lint"
assert_json_field "$output" "commands.LINT" "pnpm lint"

set_test "Node.js with pnpm — FULL_VERIFY contains &&"
assert_contains "$output" "&&" "FULL_VERIFY should chain commands"

set_test "Node.js with npm — package_manager=npm"
dir="$FIXTURE_DIR/node-npm"
mkdir -p "$dir"
touch "$dir/package-lock.json"
cat > "$dir/package.json" << 'PKGJSON'
{"scripts":{"build":"tsc","test":"jest"}}
PKGJSON
output=$(run_in "$dir")
assert_json_field "$output" "package_manager" "npm"

# ─────────────────────────────────────────
section "Rust Projects"
# ─────────────────────────────────────────

set_test "Rust — stack=rust"
dir="$FIXTURE_DIR/rust"
mkdir -p "$dir"
cat > "$dir/Cargo.toml" << 'CARGO'
[package]
name = "test-project"
version = "0.1.0"
CARGO
output=$(run_in "$dir")
assert_json_field "$output" "stack" "rust"

set_test "Rust — BUILD=cargo build"
assert_json_field "$output" "commands.BUILD" "cargo build"

set_test "Rust — UNIT_TEST=cargo test"
assert_json_field "$output" "commands.UNIT_TEST" "cargo test"

# ─────────────────────────────────────────
section "Go Projects"
# ─────────────────────────────────────────

set_test "Go — stack=go"
dir="$FIXTURE_DIR/go"
mkdir -p "$dir"
cat > "$dir/go.mod" << 'GOMOD'
module example.com/test
go 1.21
GOMOD
output=$(run_in "$dir")
assert_json_field "$output" "stack" "go"

set_test "Go — BUILD=go build ./..."
assert_json_field "$output" "commands.BUILD" "go build ./..."

# ─────────────────────────────────────────
section "Python Projects"
# ─────────────────────────────────────────

set_test "Python — stack=python"
dir="$FIXTURE_DIR/python"
mkdir -p "$dir"
cat > "$dir/pyproject.toml" << 'PYPROJ'
[tool.ruff]
select = ["E", "W"]
[tool.pytest.ini_options]
testpaths = ["tests"]
PYPROJ
output=$(run_in "$dir")
assert_json_field "$output" "stack" "python"

# ─────────────────────────────────────────
section "Makefile Projects"
# ─────────────────────────────────────────

set_test "Makefile — stack=makefile"
dir="$FIXTURE_DIR/makefile"
mkdir -p "$dir"
cat > "$dir/Makefile" << 'MAKEFILE'
build:
	echo "building"
test:
	echo "testing"
lint:
	echo "linting"
MAKEFILE
output=$(run_in "$dir")
assert_json_field "$output" "stack" "makefile"

set_test "Makefile — BUILD=make build"
assert_json_field "$output" "commands.BUILD" "make build"

# ─────────────────────────────────────────
section "Empty Directory"
# ─────────────────────────────────────────

set_test "Empty dir — stack=unknown"
dir="$FIXTURE_DIR/empty"
mkdir -p "$dir"
output=$(run_in "$dir")
assert_json_field "$output" "stack" "unknown"

set_test "Empty dir — BUILD=N/A"
assert_json_field "$output" "commands.BUILD" "N/A"

set_test "Empty dir — UNIT_TEST=N/A"
assert_json_field "$output" "commands.UNIT_TEST" "N/A"

# ─────────────────────────────────────────
# Live project tests (optional)
# ─────────────────────────────────────────

if [ "$LIVE" = "true" ]; then
  section "Live: detect-commands on omnifocus-mcp"

  PROJECT_ROOT="${PROJECT_ROOT:-$(git -C "$PLUGIN_ROOT" rev-parse --show-toplevel 2>/dev/null || echo "")}"
  if [ -n "$PROJECT_ROOT" ] && [ -f "$PROJECT_ROOT/pnpm-lock.yaml" ]; then
    output=$(run_in "$PROJECT_ROOT")

    set_test "Live — stack=nodejs"
    assert_json_field "$output" "stack" "nodejs"

    set_test "Live — package_manager=pnpm"
    assert_json_field "$output" "package_manager" "pnpm"

    set_test "Live — BUILD=pnpm build"
    assert_json_field "$output" "commands.BUILD" "pnpm build"
  else
    printf "  ${YELLOW}SKIP${RESET}: PROJECT_ROOT not detected or pnpm-lock.yaml not found\n"
  fi
fi

test_summary

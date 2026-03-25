#!/usr/bin/env bash
# detect-commands.sh — Discover project build/test/lint commands
#
# Usage: detect-commands.sh
# Output: JSON with discovered commands for any tech stack
# Exit:   0 = success, 2 = not in a project directory

set -euo pipefail

# Detect package manager for Node.js projects
detect_pkg_manager() {
  if [ -f "pnpm-lock.yaml" ]; then echo "pnpm"
  elif [ -f "yarn.lock" ]; then echo "yarn"
  elif [ -f "bun.lockb" ]; then echo "bun"
  elif [ -f "package-lock.json" ]; then echo "npm"
  else echo ""
  fi
}

# Check if a package.json script exists
has_script() {
  local script="$1"
  if [ -f "package.json" ]; then
    grep -q "\"$script\"" package.json 2>/dev/null
  else
    return 1
  fi
}

# Check if a Makefile target exists
has_make_target() {
  local target="$1"
  if [ -f "Makefile" ]; then
    grep -q "^${target}:" Makefile 2>/dev/null
  else
    return 1
  fi
}

BUILD="N/A"
TYPECHECK="N/A"
LINT="N/A"
LINT_FIX="N/A"
UNIT_TEST="N/A"
INTEGRATION_TEST="N/A"
SINGLE_FILE_TEST="N/A"
SINGLE_FILE_INTEGRATION="N/A"
STACK="unknown"

# Node.js detection
PKG=$(detect_pkg_manager)
if [ -n "$PKG" ] && [ -f "package.json" ]; then
  STACK="nodejs"
  has_script "build" && BUILD="$PKG build"
  has_script "typecheck" && TYPECHECK="$PKG typecheck"
  has_script "lint" && LINT="$PKG lint"
  has_script "lint:fix" && LINT_FIX="$PKG lint:fix"
  has_script "test" && UNIT_TEST="$PKG test"
  has_script "test:integration" && INTEGRATION_TEST="$PKG test:integration"
  has_script "test:e2e" && [ "$INTEGRATION_TEST" = "N/A" ] && INTEGRATION_TEST="$PKG test:e2e"
  # Single file test patterns
  if [ "$UNIT_TEST" != "N/A" ]; then
    SINGLE_FILE_TEST="$PKG test"
  fi
  if [ "$INTEGRATION_TEST" != "N/A" ]; then
    has_script "test:integration:file" && SINGLE_FILE_INTEGRATION="$PKG test:integration:file"
  fi

# Rust detection
elif [ -f "Cargo.toml" ]; then
  STACK="rust"
  BUILD="cargo build"
  TYPECHECK="cargo check"
  LINT="cargo clippy"
  LINT_FIX="cargo clippy --fix"
  UNIT_TEST="cargo test"
  SINGLE_FILE_TEST="cargo test"

# Go detection
elif [ -f "go.mod" ]; then
  STACK="go"
  BUILD="go build ./..."
  TYPECHECK="go vet ./..."
  LINT="golangci-lint run"
  LINT_FIX="golangci-lint run --fix"
  UNIT_TEST="go test ./..."
  SINGLE_FILE_TEST="go test"

# Python detection
elif [ -f "pyproject.toml" ] || [ -f "setup.cfg" ] || [ -f "setup.py" ]; then
  STACK="python"
  if [ -f "pyproject.toml" ] && grep -q "ruff" pyproject.toml 2>/dev/null; then
    LINT="ruff check ."
    LINT_FIX="ruff check --fix ."
  fi
  if command -v mypy >/dev/null 2>&1; then
    TYPECHECK="mypy ."
  fi
  if command -v pytest >/dev/null 2>&1 || grep -q "pytest" pyproject.toml 2>/dev/null; then
    UNIT_TEST="pytest"
    SINGLE_FILE_TEST="pytest"
    if [ -d "tests/integration" ]; then
      INTEGRATION_TEST="pytest tests/integration"
    fi
  fi

# Makefile fallback
elif [ -f "Makefile" ]; then
  STACK="makefile"
  has_make_target "build" && BUILD="make build"
  has_make_target "test" && UNIT_TEST="make test"
  has_make_target "lint" && LINT="make lint"
  has_make_target "integration" && INTEGRATION_TEST="make integration"
fi

# Build FULL_VERIFY chain
VERIFY_PARTS=()
[ "$BUILD" != "N/A" ] && VERIFY_PARTS+=("$BUILD")
[ "$TYPECHECK" != "N/A" ] && VERIFY_PARTS+=("$TYPECHECK")
[ "$LINT" != "N/A" ] && VERIFY_PARTS+=("$LINT")
[ "$UNIT_TEST" != "N/A" ] && VERIFY_PARTS+=("$UNIT_TEST")
[ "$INTEGRATION_TEST" != "N/A" ] && VERIFY_PARTS+=("$INTEGRATION_TEST")

FULL_VERIFY="N/A"
if [ ${#VERIFY_PARTS[@]} -gt 0 ]; then
  FULL_VERIFY=""
  for i in "${!VERIFY_PARTS[@]}"; do
    [ "$i" -gt 0 ] && FULL_VERIFY="$FULL_VERIFY && "
    FULL_VERIFY="$FULL_VERIFY${VERIFY_PARTS[$i]}"
  done
fi

jq -cn \
  --arg stack "$STACK" \
  --arg pkg "$PKG" \
  --arg build "$BUILD" \
  --arg typecheck "$TYPECHECK" \
  --arg lint "$LINT" \
  --arg lint_fix "$LINT_FIX" \
  --arg unit_test "$UNIT_TEST" \
  --arg integration_test "$INTEGRATION_TEST" \
  --arg single_file_test "$SINGLE_FILE_TEST" \
  --arg single_file_integration "$SINGLE_FILE_INTEGRATION" \
  --arg full_verify "$FULL_VERIFY" \
  '{
    "stack": $stack,
    "package_manager": $pkg,
    "commands": {
      "BUILD": $build,
      "TYPECHECK": $typecheck,
      "LINT": $lint,
      "LINT_FIX": $lint_fix,
      "UNIT_TEST": $unit_test,
      "INTEGRATION_TEST": $integration_test,
      "SINGLE_FILE_TEST": $single_file_test,
      "SINGLE_FILE_INTEGRATION": $single_file_integration,
      "FULL_VERIFY": $full_verify
    }
  }'

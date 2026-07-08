#!/usr/bin/env bash
# validate-spec-index-determinism.sh — Layer 1 active contract check for the
# Python-owned spec-index helper surface.
#
# XPLAT-009 removes the plugin-owned Bash generator from installed/source
# payload surfaces. The active contract is now:
#   - read-only spec-index checking is Python-authoritative in the runner
#   - write/regenerate mode is still an explicitly deferred mutation helper
#   - invoking the read-only helper does not mutate fixture trees

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/assertions.sh
source "$HERE/../lib/assertions.sh"

REPO_ROOT="$(cd "$HERE/../../.." && pwd)"
RUNNER_DIR="$REPO_ROOT/speckit-pro/speckit_pro_runner"
FIX="$HERE/fixtures/spec-index/determinism"
TPL="$REPO_ROOT/speckit-pro/skills/speckit-coach/templates/roadmap-moc-template.md"

snapshot() {
  (cd "$1" && find . -type f -exec shasum {} + | LC_ALL=C sort)
}

run_runner_request() {
  local request_file="$1"
  PYTHONPATH="$REPO_ROOT/speckit-pro" python3 -m speckit_pro_runner < "$request_file"
}

TMP="$(mktemp -d "${TMPDIR:-/tmp}/spec-index-l1.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

REGISTRY_REQ="$TMP/helper-registry.json"
cat > "$REGISTRY_REQ" <<EOF
{
  "schema_version": "1.0",
  "request_id": "l1-helper-registry",
  "helper_id": "helper-registry-dispatch",
  "operation": "helper-registry-dispatch",
  "mode": "read_only",
  "inputs": {}
}
EOF

MUTATION_REGISTRY_REQ="$TMP/mutation-registry.json"
cat > "$MUTATION_REGISTRY_REQ" <<EOF
{
  "schema_version": "1.0",
  "request_id": "l1-mutation-registry",
  "helper_id": "mutation-registry-dispatch",
  "operation": "mutation-registry-dispatch",
  "mode": "read_only",
  "inputs": {}
}
EOF

CHECK_REQ="$TMP/generate-spec-index-check.json"
cat > "$CHECK_REQ" <<EOF
{
  "schema_version": "1.0",
  "request_id": "l1-generate-spec-index-check",
  "helper_id": "generate-spec-index-check",
  "operation": "generate-spec-index-check",
  "mode": "read_only",
  "inputs": {
    "repo_root": "tests/speckit-pro/layer1-structural/fixtures/spec-index/determinism"
  }
}
EOF

# ───────────────────────────────────────────────────────────────────────────
section "Runner-owned spec-index helper contract"
# ───────────────────────────────────────────────────────────────────────────

set_test "runner package exists at the contracted path"
assert_file_exists "$RUNNER_DIR/__main__.py" "FAIL: runner entrypoint not found at $RUNNER_DIR/__main__.py"

registry_json="$(run_runner_request "$REGISTRY_REQ")"

set_test "read-only registry dispatch succeeds"
assert_contains "$registry_json" '"status":"ok"'

set_test "generate-spec-index-check is registered"
assert_contains "$registry_json" '"helper_id":"generate-spec-index-check"'

set_test "generate-spec-index-check is Python-authoritative"
assert_contains "$registry_json" '"promotion_status":"python_authoritative"'

mutation_registry_json="$(run_runner_request "$MUTATION_REGISTRY_REQ")"

set_test "mutation registry dispatch succeeds"
assert_contains "$mutation_registry_json" '"status":"ok"'

set_test "generate-spec-index-write is registered as deferred"
assert_contains "$mutation_registry_json" '"helper_id":"generate-spec-index-write"'
assert_contains "$mutation_registry_json" '"promotion_status":"deferred"'

# ───────────────────────────────────────────────────────────────────────────
section "Read-only helper invocation is deterministic and non-mutating"
# ───────────────────────────────────────────────────────────────────────────

snap_before="$(snapshot "$FIX")"
check_json="$(run_runner_request "$CHECK_REQ")"
snap_after="$(snapshot "$FIX")"

set_test "generate-spec-index-check request succeeds"
assert_contains "$check_json" '"status":"ok"'

set_test "generate-spec-index-check reports the helper id"
assert_contains "$check_json" '"helper_id":"generate-spec-index-check"'

set_test "generate-spec-index-check uses shell:false"
assert_contains "$check_json" '"shell":false'

set_test "generate-spec-index-check records writes_state:false"
assert_contains "$check_json" '"writes_state":false'

set_test "generate-spec-index-check leaves fixture bytes unchanged"
assert_eq "$snap_before" "$snap_after" "read-only helper must not mutate spec-index fixtures"

# ───────────────────────────────────────────────────────────────────────────
section "Sentinel seam — roadmap-MOC template still exposes INDEX markers"
# ───────────────────────────────────────────────────────────────────────────

set_test "roadmap-MOC template exists at the contracted path"
assert_file_exists "$TPL" "FAIL: roadmap-MOC template not found at $TPL"

tpl_index_start="$(grep -F 'GENERATED:INDEX:START' "$TPL" || true)"
tpl_index_end="$(grep -F 'GENERATED:INDEX:END' "$TPL" || true)"

set_test "template INDEX sentinels are present"
if [ -n "$tpl_index_start" ] && [ -n "$tpl_index_end" ]; then
  _pass
else
  _fail "missing INDEX sentinel in roadmap-MOC template"
fi

set_test "template INDEX:START keeps the sentinel grammar"
assert_eq '<!-- GENERATED:INDEX:START (do not edit; regenerated by generate-spec-index) -->' "$tpl_index_start" "template INDEX:START sentinel drifted"

set_test "template INDEX:END keeps the sentinel grammar"
assert_eq '<!-- GENERATED:INDEX:END -->' "$tpl_index_end" "template INDEX:END sentinel drifted"

test_summary

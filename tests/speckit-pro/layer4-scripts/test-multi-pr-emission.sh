#!/usr/bin/env bash
# test-multi-pr-emission.sh - PRSG-009 foundation tests for safe multi-PR emission entrypoint.

set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

TEST_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
SCRIPT="$REPO_ROOT/speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh"
FIXTURE_ROOT="$TEST_DIR/fixtures/multi-pr-emission"
MARKER_FIXTURE_ROOT="$TEST_DIR/fixtures/marker-plan"

SANDBOX=$(mktemp -d)
trap 'rm -rf "$SANDBOX"' EXIT

json_check() {
  local json="$1" expr="$2" msg="$3"
  local file="$SANDBOX/json-check.json"
  printf '%s' "$json" > "$file"
  if python3 - "$file" "$expr" >/dev/null 2>&1 <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as fh:
    data = json.load(fh)

expr = sys.argv[2]
safe_builtins = {"any": any, "all": all, "len": len, "list": list, "range": range, "sorted": sorted}
if not eval(expr, {"__builtins__": safe_builtins}, {"data": data}):
    raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

assert_pr_create_uses_packet() {
  local commands_json="$1" packet_json="$2" slice_id="$3" msg="$4"
  local commands_file="$SANDBOX/pr-create-commands.$RANDOM.json"
  local packet_file="$SANDBOX/pr-create-packet.$RANDOM.json"
  printf '%s' "$commands_json" > "$commands_file"
  printf '%s' "$packet_json" > "$packet_file"
  if python3 - "$commands_file" "$packet_file" "$slice_id" >/dev/null 2>&1 <<'PY'
import json
import sys

commands_path, packet_path, slice_id = sys.argv[1:4]
with open(commands_path, encoding="utf-8") as fh:
    commands = json.load(fh)
with open(packet_path, encoding="utf-8") as fh:
    packet = json.load(fh)

ops = [
    op for op in commands["operations"]
    if op.get("action") == "gh_pr_create" and op.get("slice_id") == slice_id
]
if len(ops) != 1:
    raise SystemExit(1)

command = ops[0].get("command")
if not isinstance(command, list):
    raise SystemExit(1)

def flag_value(flag):
    indexes = [idx for idx, value in enumerate(command[:-1]) if value == flag]
    if len(indexes) != 1:
        raise SystemExit(1)
    value = command[indexes[0] + 1]
    if not isinstance(value, str) or value == "":
        raise SystemExit(1)
    return value

expected = {
    "--base": packet["target"]["base_branch"],
    "--head": packet["target"]["head_branch"],
    "--title": packet["generated_title"]["value"],
    "--body-file": packet["body_file"],
}

for flag, expected_value in expected.items():
    actual = flag_value(flag)
    if flag == "--body-file":
        if actual != expected_value and not actual.endswith("/" + expected_value):
            raise SystemExit(1)
    elif actual != expected_value:
        raise SystemExit(1)
PY
  then
    _pass
  else
    _fail "$msg"
  fi
}

run_emission() {
  local out_var="$1" err_var="$2"
  shift 2
  local stdout_file="$SANDBOX/stdout.$RANDOM"
  local stderr_file="$SANDBOX/stderr.$RANDOM"
  local rc=0
  "$@" >"$stdout_file" 2>"$stderr_file" || rc=$?
  printf -v "$out_var" '%s' "$(cat "$stdout_file")"
  printf -v "$err_var" '%s' "$(cat "$stderr_file")"
  return "$rc"
}

section "script presence"

set_test "multi-pr-emission.sh exists"
assert_file_exists "$SCRIPT"

set_test "multi-pr-emission.sh is executable"
assert_file_executable "$SCRIPT"

script_source=$(cat "$SCRIPT")

set_test "Emitter does not hardcode current PRSG-012 marker title descriptions"
assert_not_contains "$script_source" "Generate packet-owned conventional PR titles"

set_test "Emitter does not hardcode current PRSG-012 reviewer-body title"
assert_not_contains "$script_source" "Render plain-English reviewer PR body evidence"

section "layer-plan and state validation"

valid_plan="$FIXTURE_ROOT/layer-plans/valid-three-slice.json"
single_slice_plan="$FIXTURE_ROOT/layer-plans/valid-single-slice.json"
invalid_plan="$FIXTURE_ROOT/layer-plans/invalid-status.json"
input_error_plan="$FIXTURE_ROOT/layer-plans/input-error-status.json"
malformed_plan="$FIXTURE_ROOT/layer-plans/malformed.json"
empty_state="$FIXTURE_ROOT/emission-state/empty-autopilot-state.json"
duplicate_state="$FIXTURE_ROOT/emission-state/duplicate-slice-keys.json"
full_evidence="$SANDBOX/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
marker_full_evidence="$SANDBOX/specs/prsg-013-reviewability-markers/.process/emission/full-regression.txt"
custom_feature_plan="$SANDBOX/custom-feature-plan.json"
custom_full_evidence="$SANDBOX/specs/prsg-999-custom-feature/.process/emission/full-regression.txt"
spec_future_plan="$SANDBOX/spec-future-plan.json"
spec_future_evidence="$SANDBOX/specs/spec-014c-future-title-contract/.process/emission/full-regression.txt"
wrong_feature_evidence="$SANDBOX/specs/prsg-009-multi-pr-emission/.process/emission/wrong-feature.txt"
declared_changed_files="$SANDBOX/declared-changed-files.txt"
scope_violation_files="$SANDBOX/scope-violation-files.txt"
marker_declared_changed_files="$SANDBOX/marker-declared-changed-files.txt"
marker_scope_violation_files="$SANDBOX/marker-scope-violation-files.txt"
prsg012_marker_plan="$REPO_ROOT/specs/prsg-012-reviewer-ready-pr-packet-contract/.process/marker-plan/pr-marker-plan.json"
prsg012_split_result="$REPO_ROOT/specs/prsg-012-reviewer-ready-pr-packet-contract/.process/marker-plan/final-marker-split-result.json"
prsg012_full_evidence="$SANDBOX/specs/prsg-012-reviewer-ready-pr-packet-contract/.process/emission/full-regression.log"

mkdir -p "$(dirname "$full_evidence")"
printf '%s\n' 'DEFAULT_VERIFY passed for PRSG-009 fixture' > "$full_evidence"
mkdir -p "$(dirname "$marker_full_evidence")"
printf '%s\n' 'DEFAULT_VERIFY passed for PRSG-013 marker fixture' > "$marker_full_evidence"
mkdir -p "$(dirname "$prsg012_full_evidence")"
printf '%s\n' 'DEFAULT_VERIFY passed for PRSG-012 marker title fixture' > "$prsg012_full_evidence"
mkdir -p "$(dirname "$custom_full_evidence")" "$(dirname "$spec_future_evidence")" "$(dirname "$wrong_feature_evidence")"
printf '%s\n' 'DEFAULT_VERIFY passed for custom feature fixture' > "$custom_full_evidence"
printf '%s\n' 'DEFAULT_VERIFY passed for future SPEC fixture' > "$spec_future_evidence"
printf '%s\n' 'wrong feature evidence path' > "$wrong_feature_evidence"
jq '.feature_dir = "specs/prsg-999-custom-feature"' "$valid_plan" > "$custom_feature_plan"
jq '.feature_dir = "specs/spec-014c-future-title-contract"' "$valid_plan" > "$spec_future_plan"
cat > "$declared_changed_files" <<'EOF'
tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
speckit-pro/skills/speckit-autopilot/scripts/generate-pr-body.sh
EOF
cat > "$scope_violation_files" <<'EOF'
tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
docs/unplanned-runtime-change.md
EOF
cat > "$marker_declared_changed_files" <<'EOF'
tests/speckit-pro/layer4-scripts/fixtures/marker-plan/valid-pr-marker-plan.json
tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh
speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
speckit-pro/skills/speckit-autopilot/contracts/multi-pr-emission-state.schema.json
EOF
cat > "$marker_scope_violation_files" <<'EOF'
speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh
docs/unplanned-marker-change.md
EOF

set_test "invalid layer-plan status blocks before mutation"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$invalid_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef || result=$?
assert_eq "2" "$result" "exit code"

set_test "invalid layer-plan status emits deterministic stderr"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: layer plan status invalid_plan"

set_test "input-error layer-plan status blocks before mutation"
input_error_candidate_dir="$SANDBOX/input-error-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$input_error_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --candidate-dir "$input_error_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"

set_test "input-error layer-plan status does not write command capture"
assert_file_not_exists "$input_error_candidate_dir/commands.candidate.json"

set_test "malformed layer-plan JSON blocks before mutation"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$malformed_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef || result=$?
assert_eq "2" "$result" "exit code"

set_test "duplicate state slice_id values are rejected"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$duplicate_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef || result=$?
assert_eq "2" "$result" "exit code"

set_test "duplicate state rejection names the duplicate key"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: duplicate state slice_id foundation"

set_test "valid emission requires full regression evidence"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef || result=$?
assert_eq "2" "$result" "exit code"

set_test "missing full regression evidence emits deterministic stderr"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: missing required option --full-verification-evidence"

set_test "invalid slice branch names are rejected before command capture"
bad_branch_candidate_dir="$SANDBOX/bad-branch-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$empty_state" \
  --feature-branch "bad branch" \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$full_evidence" \
  --candidate-dir "$bad_branch_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"

set_test "invalid slice branch names do not write command capture"
assert_file_not_exists "$bad_branch_candidate_dir/commands.candidate.json"

set_test "full regression evidence path is derived from feature_dir"
custom_candidate_dir="$SANDBOX/custom-feature-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$custom_feature_plan" \
  --state "$empty_state" \
  --feature-branch prsg-999-custom-feature \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$custom_full_evidence" \
  --candidate-dir "$custom_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

set_test "future SPEC dry run derives title scope from feature_dir"
spec_future_candidate_dir="$SANDBOX/spec-future-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$spec_future_plan" \
  --state "$empty_state" \
  --feature-branch spec-014c-future-title-contract \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$spec_future_evidence" \
  --candidate-dir "$spec_future_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

spec_future_commands_json="$(cat "$spec_future_candidate_dir/commands.candidate.json" 2>/dev/null || true)"

set_test "future SPEC dry run uses derived SPEC scope for every PR title"
json_check "$spec_future_commands_json" \
  "len([op for op in data['operations'] if op['action'] == 'gh_pr_create']) == 3 and all(op['title'].startswith('feat(SPEC-014C): ') for op in data['operations'] if op['action'] == 'gh_pr_create')" \
  "future SPEC dry run should use SPEC-014C title scope"

set_test "future SPEC dry run does not use current or fallback scope"
json_check "$spec_future_commands_json" \
  "not any(('PRSG-012' in op.get('title', '') or 'feat(speckit-pro):' in op.get('title', '')) for op in data['operations'] if op['action'] == 'gh_pr_create')" \
  "future SPEC dry run should not use PRSG-012 or plugin fallback title scope"

set_test "wrong feature evidence path exits 2"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$custom_feature_plan" \
  --state "$empty_state" \
  --feature-branch prsg-999-custom-feature \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$wrong_feature_evidence" \
  --candidate-dir "$SANDBOX/wrong-feature-candidates" || result=$?
assert_eq "2" "$result" "exit code"

set_test "wrong feature evidence path names derived emission directory"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: full verification evidence must be under specs/prsg-999-custom-feature/.process/emission/"

section "candidate JSON writes"

candidate_dir="$SANDBOX/candidates"
mkdir -p "$candidate_dir"

set_test "valid foundation dry run writes candidate JSON files"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$full_evidence" \
  --changed-files "$declared_changed_files" \
  --candidate-dir "$candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

candidate_state="$candidate_dir/multi-pr-emission-state.candidate.json"
candidate_prs="$candidate_dir/prs.candidate.json"
candidate_commands="$candidate_dir/commands.candidate.json"
foundation_packet="$candidate_dir/slice-packets/foundation.json"
us1_packet="$candidate_dir/slice-packets/us1.json"
us2_packet="$candidate_dir/slice-packets/us2.json"

set_test "candidate state file exists"
assert_file_exists "$candidate_state"

set_test "candidate PRS manifest file exists"
assert_file_exists "$candidate_prs"

set_test "candidate command capture file exists"
assert_file_exists "$candidate_commands"

set_test "candidate slice packets exist"
if [ -f "$foundation_packet" ] && [ -f "$us1_packet" ] && [ -f "$us2_packet" ]; then
  _pass
else
  _fail "expected slice packets for foundation, us1, and us2"
fi

state_json="$(cat "$candidate_state" 2>/dev/null || true)"
prs_json="$(cat "$candidate_prs" 2>/dev/null || true)"
commands_json="$(cat "$candidate_commands" 2>/dev/null || true)"
foundation_packet_json="$(cat "$foundation_packet" 2>/dev/null || true)"
us1_packet_json="$(cat "$us1_packet" 2>/dev/null || true)"
us2_packet_json="$(cat "$us2_packet" 2>/dev/null || true)"

set_test "candidate state is resume-safe and non-mutating"
json_check "$state_json" \
  "data['multi_pr_emission']['status'] == 'pending' and data['multi_pr_emission']['next_slice_id'] == 'foundation' and data['multi_pr_emission']['slices'][0]['status'] == 'pending' and 'pr' not in data['multi_pr_emission']['slices'][0]" \
  "candidate state should be pending/resumable and contain no PR record"

set_test "candidate state preserves plan order as review_order"
json_check "$state_json" \
  "[s['slice_id'] for s in data['multi_pr_emission']['slices']] == ['foundation', 'us1', 'us2'] and [s['review_order'] for s in data['multi_pr_emission']['slices']] == [1, 2, 3]" \
  "candidate slices should preserve layer-plan order"

set_test "candidate state records Style B branch/base topology"
json_check "$state_json" \
  "[s['expected_branch'] for s in data['multi_pr_emission']['slices']] == ['prsg-009-multi-pr-emission/01-foundation', 'prsg-009-multi-pr-emission/02-us1', 'prsg-009-multi-pr-emission/03-us2'] and [s['expected_base_branch'] for s in data['multi_pr_emission']['slices']] == ['main', 'prsg-009-multi-pr-emission/01-foundation', 'prsg-009-multi-pr-emission/02-us1']" \
  "candidate slices should use Style B base ordering"

set_test "candidate PRS manifest is schemaVersion 2 with no opened PR rows yet"
json_check "$prs_json" \
  "data['schemaVersion'] == 2 and data['records'] == []" \
  "foundation candidate PRS manifest should not persist fake PR rows"

set_test "candidate command capture preserves branch push PR operation order"
json_check "$commands_json" \
  "[op['action'] for op in data['operations']] == ['git_branch', 'git_push', 'validate_pr_packet', 'gh_pr_create', 'git_branch', 'git_push', 'validate_pr_packet', 'gh_pr_create', 'git_branch', 'git_push', 'validate_pr_packet', 'gh_pr_create']" \
  "dry-run operation capture should preserve branch/push/validate/PR ordering per slice"

set_test "candidate command capture validates each packet before PR creation"
json_check "$commands_json" \
  "data['operations'][2]['action'] == 'validate_pr_packet' and data['operations'][3]['action'] == 'gh_pr_create' and data['operations'][2]['slice_id'] == data['operations'][3]['slice_id'] and data['operations'][6]['action'] == 'validate_pr_packet' and data['operations'][7]['action'] == 'gh_pr_create' and data['operations'][6]['slice_id'] == data['operations'][7]['slice_id'] and data['operations'][10]['action'] == 'validate_pr_packet' and data['operations'][11]['action'] == 'gh_pr_create' and data['operations'][10]['slice_id'] == data['operations'][11]['slice_id']" \
  "dry-run operation capture should place validate_pr_packet immediately before each gh pr create"

set_test "candidate command capture uses explicit gh pr create base head body-file"
json_check "$commands_json" \
  "[op['command'][0:8] for op in data['operations'] if op['action'] == 'gh_pr_create'] == [['gh', 'pr', 'create', '--base', 'main', '--head', 'prsg-009-multi-pr-emission/01-foundation', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-009-multi-pr-emission/01-foundation', '--head', 'prsg-009-multi-pr-emission/02-us1', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-009-multi-pr-emission/02-us1', '--head', 'prsg-009-multi-pr-emission/03-us2', '--body-file']]" \
  "gh pr create must pass explicit --base --head --body-file"

set_test "candidate foundation PR create command uses packet target title and body"
assert_pr_create_uses_packet "$commands_json" "$foundation_packet_json" "foundation" \
  "foundation gh pr create should use packet --base, --head, --title, and --body-file values"

set_test "candidate us1 PR create command uses packet target title and body"
assert_pr_create_uses_packet "$commands_json" "$us1_packet_json" "us1" \
  "us1 gh pr create should use packet --base, --head, --title, and --body-file values"

set_test "candidate us2 PR create command uses packet target title and body"
assert_pr_create_uses_packet "$commands_json" "$us2_packet_json" "us2" \
  "us2 gh pr create should use packet --base, --head, --title, and --body-file values"

set_test "candidate command capture records declared scope guard"
json_check "$commands_json" \
  "data['declared_scope_guard']['status'] == 'passed' and data['declared_scope_guard']['changed_files_count'] == 3" \
  "declared file-scope guard should pass declared changed files"

set_test "slice packet carries full regression evidence"
json_check "$foundation_packet_json" \
  "data['full_verification_evidence'] == '$full_evidence' and data['review_order'] == 1 and data['base_branch'] == 'main' and data['head_branch'] == 'prsg-009-multi-pr-emission/01-foundation'" \
  "slice packet should copy the full regression evidence path and branch refs"

set_test "slice packet preserves layer-plan warnings for affected slice"
json_check "$foundation_packet_json" \
  "any('Foundation fixture keeps warnings' in warning for warning in data['warnings'])" \
  "affected slice packet should keep layer-plan warnings"

set_test "unaffected slice packet has no copied warnings"
json_check "$us1_packet_json" \
  "data['warnings'] == []" \
  "unaffected slice packet should not receive unrelated warnings"

set_test "stdout identifies safe foundation mode and schema constants"
json_check "$output" \
  "data['script'] == 'multi-pr-emission' and data['status'] == 'validated' and data['mutation']['branches'] == False and data['mutation']['pull_requests'] == False and data['emission']['slice_count'] == 3 and 'multi_pr_emission_state' in data['schema_paths']" \
  "stdout should describe the safe non-mutating foundation result"

set_test "successful foundation validation emits no stderr"
assert_eq "" "$stderr_output" "stderr"

section "single-slice emission planning"

single_candidate_dir="$SANDBOX/single-candidates"

set_test "single-slice dry run writes one candidate slice"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$single_slice_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$full_evidence" \
  --candidate-dir "$single_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

single_state_json="$(cat "$single_candidate_dir/multi-pr-emission-state.candidate.json" 2>/dev/null || true)"
single_commands_json="$(cat "$single_candidate_dir/commands.candidate.json" 2>/dev/null || true)"
single_packet_json="$(cat "$single_candidate_dir/slice-packets/us1.json" 2>/dev/null || true)"

set_test "single-slice state uses same Style B contract"
json_check "$single_state_json" \
  "len(data['multi_pr_emission']['slices']) == 1 and data['multi_pr_emission']['slices'][0]['slice_id'] == 'us1' and data['multi_pr_emission']['slices'][0]['expected_branch'] == 'prsg-009-multi-pr-emission/01-us1' and data['multi_pr_emission']['slices'][0]['expected_base_branch'] == 'main'" \
  "single-slice emission should not fall back to flattened PR behavior"

set_test "single-slice command capture has one explicit PR create"
json_check "$single_commands_json" \
  "[op['command'][0:8] for op in data['operations'] if op['action'] == 'gh_pr_create'] == [['gh', 'pr', 'create', '--base', 'main', '--head', 'prsg-009-multi-pr-emission/01-us1', '--body-file']]" \
  "single-slice emission should still use explicit --base --head --body-file"

set_test "single-slice PR create command uses packet target title and body"
assert_pr_create_uses_packet "$single_commands_json" "$single_packet_json" "us1" \
  "single-slice gh pr create should use packet --base, --head, --title, and --body-file values"

section "declared file-scope guard"

scope_candidate_dir="$SANDBOX/scope-candidates"

set_test "undeclared changed files block emission before command capture"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$empty_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$full_evidence" \
  --changed-files "$scope_violation_files" \
  --candidate-dir "$scope_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"

set_test "undeclared changed files emit deterministic stderr"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: changed file outside declared slice scope: docs/unplanned-runtime-change.md"

set_test "undeclared changed files do not write command capture"
assert_file_not_exists "$scope_candidate_dir/commands.candidate.json"

section "PRSG-013 marker-aware emission"

valid_marker_plan="$MARKER_FIXTURE_ROOT/valid-pr-marker-plan.json"
stale_marker_plan="$MARKER_FIXTURE_ROOT/stale-pr-marker-plan.json"
placeholder_marker_plan="$MARKER_FIXTURE_ROOT/placeholder-pr-marker-plan.json"
malformed_marker_plan="$MARKER_FIXTURE_ROOT/malformed-pr-marker-plan.json"
marker_split_result="$MARKER_FIXTURE_ROOT/final-marker-split-result.json"
single_atomic_split_result="$MARKER_FIXTURE_ROOT/hazard-single-atomic-split-result.json"
unreleasable_split_result="$MARKER_FIXTURE_ROOT/hazard-unreleasable-split-result.json"
navigable_split_result="$MARKER_FIXTURE_ROOT/navigable-releasable-split-result.json"
mismatched_split_result="$MARKER_FIXTURE_ROOT/mismatched-marker-split-result.json"
order_mismatch_split_result="$MARKER_FIXTURE_ROOT/order-mismatch-split-result.json"

marker_candidate_dir="$SANDBOX/marker-candidates"

set_test "marker-aware dry run emits one marker packet per marker in review order"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --changed-files "$marker_declared_changed_files" \
  --candidate-dir "$marker_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

marker_state_json="$(cat "$marker_candidate_dir/multi-pr-emission-state.candidate.json" 2>/dev/null || true)"
marker_commands_json="$(cat "$marker_candidate_dir/commands.candidate.json" 2>/dev/null || true)"
marker_foundation_packet="$marker_candidate_dir/marker-packets/foundation.json"
marker_us1_packet="$marker_candidate_dir/marker-packets/us1.json"
marker_us2_packet="$marker_candidate_dir/marker-packets/us2-part1.json"
marker_foundation_packet_json="$(cat "$marker_foundation_packet" 2>/dev/null || true)"
marker_us1_packet_json="$(cat "$marker_us1_packet" 2>/dev/null || true)"
marker_us2_packet_json="$(cat "$marker_us2_packet" 2>/dev/null || true)"

set_test "marker packet files are emitted for every planned marker"
if [ -f "$marker_foundation_packet" ] && [ -f "$marker_us1_packet" ] && [ -f "$marker_us2_packet" ]; then
  _pass
else
  _fail "expected marker packets for foundation, us1, and us2-part1"
fi

set_test "marker candidate state records marker mode and marker review order"
json_check "$marker_state_json" \
  "data['multi_pr_emission']['emission_mode'] == 'marker' and data['multi_pr_emission']['route'] == 'marker_split' and [s['marker_id'] for s in data['multi_pr_emission']['slices']] == ['foundation', 'us1', 'us2-part1'] and [s['review_order'] for s in data['multi_pr_emission']['slices']] == [1, 2, 3]" \
  "marker candidate state should preserve marker review order"

set_test "marker command capture preserves marker branch PR operation order"
json_check "$marker_commands_json" \
  "[op['slice_id'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['foundation', 'us1', 'us2-part1'] and [op['command'][0:8] for op in data['operations'] if op['action'] == 'gh_pr_create'] == [['gh', 'pr', 'create', '--base', 'main', '--head', 'prsg-013-reviewability-markers/01-foundation', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-013-reviewability-markers/01-foundation', '--head', 'prsg-013-reviewability-markers/02-us1', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-013-reviewability-markers/02-us1', '--head', 'prsg-013-reviewability-markers/03-us2-part1', '--body-file']]" \
  "marker dry-run command capture should preserve marker branch order"

set_test "marker packet shape includes marker IDs, final split evidence, and checkpoint evidence"
json_check "$marker_foundation_packet_json" \
  "data['slice_id'] == 'foundation' and data['marker_id'] == 'foundation' and data['source_marker_ids'] == ['foundation'] and data['route'] == 'marker_split' and data['marker_split_evidence'] == '$marker_split_result' and data['implementation_checkpoint_evidence'] == 'specs/prsg-013-reviewability-markers/.process/markers/foundation-checkpoint.md' and data['warnings'][0]['code'] == 'FOUNDATION_SIZE_WARN'" \
  "foundation marker packet should carry marker-specific evidence and warnings"

set_test "marker packets carry declared files and tests from marker scope"
json_check "$marker_us1_packet_json" \
  "data['declared_files'] == ['speckit-pro/skills/speckit-autopilot/scripts/multi-pr-emission.sh'] and data['declared_tests'] == ['bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh']" \
  "us1 marker packet should use marker declared file/test scope"

set_test "marker packet validation does not require PRSG-012 title/body fields"
json_check "$marker_us2_packet_json" \
  "'title' not in data and 'body' not in data and data['marker_id'] == 'us2-part1'" \
  "marker packet validation should not implement reviewer-ready title/body checks"

set_test "marker-aware stdout identifies marker mode and marker count"
json_check "$output" \
  "data['script'] == 'multi-pr-emission' and data['status'] == 'validated' and data['emission']['mode'] == 'marker' and data['emission']['route'] == 'marker_split' and data['emission']['marker_count'] == 3" \
  "stdout should describe marker-aware dry-run result"

section "PRSG-012 marker title regression"

prsg012_candidate_dir="$SANDBOX/prsg012-marker-candidates"

set_test "PRSG-012 marker dry run normalizes generic story labels into public titles"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$prsg012_marker_plan" \
  --marker-split-result "$prsg012_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-012-reviewer-ready-pr-packet-contract \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$prsg012_full_evidence" \
  --candidate-dir "$prsg012_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

prsg012_commands_json="$(cat "$prsg012_candidate_dir/commands.candidate.json" 2>/dev/null || true)"
prsg012_us1_body="$(cat "$prsg012_candidate_dir/pr-bodies/us1.md" 2>/dev/null || true)"

set_test "PRSG-012 marker commands use strict plain-English titles"
json_check "$prsg012_commands_json" \
  "[op['title'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['feat(PRSG-012): Add reviewer packet validation contract', 'feat(PRSG-012): Generate packet-owned conventional PR titles', 'feat(PRSG-012): Render plain-English reviewer PR body evidence', 'feat(PRSG-012): Block invalid PR packets before creation', 'feat(PRSG-012): Protect editable PR body prose']" \
  "PRSG-012 marker PR titles should name the actual reviewer-visible change"

set_test "PRSG-012 marker commands reject raw foundation/story labels"
json_check "$prsg012_commands_json" \
  "not any(('Foundation' in op.get('title', '') or 'User Story' in op.get('title', '') or 'Priority:' in op.get('title', '') or op.get('title', '').endswith(': us1')) for op in data['operations'] if op['action'] == 'gh_pr_create')" \
  "PRSG-012 marker PR titles must not expose raw marker labels"

set_test "PRSG-012 marker candidate body explains the change"
assert_contains "$prsg012_us1_body" "This PR covers one reviewer-ready slice: Generate packet-owned conventional PR titles."

set_test "PRSG-012 marker candidate body omits packet-mechanics prose"
assert_not_contains "$prsg012_us1_body" 'Prepared `'

set_test "PRSG-012 marker candidate body does not start with empty host headings"
assert_not_contains "$prsg012_us1_body" "# What changed"

set_test "single-atomic hazard collapses marker emission to one full-spec packet"
single_atomic_candidate_dir="$SANDBOX/single-atomic-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$single_atomic_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$single_atomic_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"

single_atomic_packet_json="$(cat "$single_atomic_candidate_dir/marker-packets/full-spec.json" 2>/dev/null || true)"
single_atomic_state_json="$(cat "$single_atomic_candidate_dir/multi-pr-emission-state.candidate.json" 2>/dev/null || true)"

set_test "single-atomic full-spec packet preserves ordered source marker ids"
json_check "$single_atomic_packet_json" \
  "data['marker_id'] == 'full-spec' and data['source_marker_ids'] == ['foundation', 'us1', 'us2-part1'] and data['route'] == 'hazard_collapsed' and data['review_order'] == 1 and data['source_marker_checkpoints'] == ['specs/prsg-013-reviewability-markers/.process/markers/foundation-checkpoint.md', 'specs/prsg-013-reviewability-markers/.process/markers/us1-checkpoint.md', 'specs/prsg-013-reviewability-markers/.process/markers/us2-part1-checkpoint.md'] and data['warnings'][0]['code'] == 'HAZARD_COLLAPSE'" \
  "hazard-collapsed packet should preserve original marker IDs and checkpoints"

set_test "single-atomic candidate state emits one full-spec slice"
json_check "$single_atomic_state_json" \
  "data['multi_pr_emission']['route'] == 'hazard_collapsed' and [s['marker_id'] for s in data['multi_pr_emission']['slices']] == ['full-spec'] and data['multi_pr_emission']['slices'][0]['source_marker_ids'] == ['foundation', 'us1', 'us2-part1']" \
  "hazard-collapsed state should contain one full-spec emission slice"

set_test "unreleasable hazard also collapses to full-spec"
unreleasable_candidate_dir="$SANDBOX/unreleasable-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$unreleasable_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$unreleasable_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"
assert_file_exists "$unreleasable_candidate_dir/marker-packets/full-spec.json"

set_test "one-navigable releasable route does not collapse by itself"
navigable_candidate_dir="$SANDBOX/navigable-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$navigable_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$navigable_candidate_dir" || result=$?
assert_eq "0" "$result" "exit code"
navigable_state_json="$(cat "$navigable_candidate_dir/multi-pr-emission-state.candidate.json" 2>/dev/null || true)"
json_check "$navigable_state_json" \
  "data['multi_pr_emission']['route'] == 'marker_split' and [s['marker_id'] for s in data['multi_pr_emission']['slices']] == ['foundation', 'us1', 'us2-part1']" \
  "one-navigable-PR with releasable=true should keep marker-split emission"
assert_file_not_exists "$navigable_candidate_dir/marker-packets/full-spec.json"

set_test "stale marker plan stops before command capture or PR body generation"
invalid_marker_candidate_dir="$SANDBOX/stale-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$stale_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$invalid_marker_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: marker plan status stale"
assert_file_not_exists "$invalid_marker_candidate_dir/commands.candidate.json"
assert_file_not_exists "$invalid_marker_candidate_dir/pr-bodies"

set_test "malformed marker plan stops before side effects"
malformed_marker_candidate_dir="$SANDBOX/malformed-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$malformed_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$malformed_marker_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: invalid marker plan JSON"
assert_file_not_exists "$malformed_marker_candidate_dir/commands.candidate.json"

set_test "placeholder-filled marker packet scope stops before side effects"
placeholder_marker_candidate_dir="$SANDBOX/placeholder-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$placeholder_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$placeholder_marker_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: invalid marker packet shape: placeholder declared file path for foundation"
assert_file_not_exists "$placeholder_marker_candidate_dir/commands.candidate.json"

set_test "marker split result with unknown marker stops before side effects"
mismatched_marker_candidate_dir="$SANDBOX/mismatched-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$mismatched_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$mismatched_marker_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: marker split result references unknown marker us9"
assert_file_not_exists "$mismatched_marker_candidate_dir/commands.candidate.json"

set_test "marker split result with order mismatch stops before side effects"
order_mismatch_candidate_dir="$SANDBOX/order-mismatch-marker-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$order_mismatch_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$order_mismatch_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: marker split result review_order mismatch for us1"
assert_file_not_exists "$order_mismatch_candidate_dir/commands.candidate.json"

set_test "marker changed-file scope mismatch stops before side effects"
marker_scope_candidate_dir="$SANDBOX/marker-scope-candidates"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --changed-files "$marker_scope_violation_files" \
  --candidate-dir "$marker_scope_candidate_dir" || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: changed file outside declared marker scope: docs/unplanned-marker-change.md"
assert_file_not_exists "$marker_scope_candidate_dir/commands.candidate.json"

set_test "live marker emission rejects candidate dry-run mode"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --candidate-dir "$SANDBOX/live-candidates" \
  --live || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: --live cannot be combined with --candidate-dir"

set_test "live marker emission rejects fixture mode"
live_pr_fixture="$SANDBOX/live-pr-fixture.json"
printf '%s\n' '{"existing":[],"created":[]}' > "$live_pr_fixture"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$empty_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$marker_full_evidence" \
  --pr-fixture "$live_pr_fixture" \
  --live || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: --live cannot be combined with --pr-fixture"

make_marker_persist_repo() {
  local root="$1"
  mkdir -p \
    "$root/docs/ai/specs/.process" \
    "$root/specs/prsg-013-reviewability-markers/.process/emission" \
    "$root/specs/prsg-013-reviewability-markers/.process"
  printf '{}\n' > "$root/docs/ai/specs/.process/autopilot-state.json"
  cat > "$root/specs/prsg-013-reviewability-markers/SPEC-MOC.md" <<'EOF'
---
structureVersion: 1
spec_id: PRSG-013
---

# PRSG-013 Fixture

<!-- GENERATED:PRS:START (do not edit; regenerated by generate-spec-index.sh) -->
<!-- GENERATED:PRS:END -->
EOF
  cat > "$root/docs/ai/specs/.process/PRSG-013-workflow.md" <<'EOF'
# PRSG-013 Workflow Fixture

## Phase 7: Implement
EOF
  printf '%s\n' 'PRSG-013 full regression fixture passed' > "$root/specs/prsg-013-reviewability-markers/.process/emission/full-regression.txt"
  git -C "$root" init >/dev/null 2>&1
}

make_live_marker_success_repo() {
  local root="$1" remote="$2"
  make_marker_persist_repo "$root"
  git -C "$root" config user.email "test@test"
  git -C "$root" config user.name "SpecKit Test"
  git -C "$root" config commit.gpgsign false
  git -C "$root" checkout -q -b main
  git -C "$root" add -A
  git -C "$root" commit -q -m "base fixture"

  git -C "$root" checkout -q -b fixture-feature
  mkdir -p "$root/specs/prsg-013-reviewability-markers/.process/markers"

  printf '%s\n' 'foundation checkpoint complete' > "$root/specs/prsg-013-reviewability-markers/.process/markers/foundation-checkpoint.md"
  git -C "$root" add -A
  git -C "$root" commit -q -m "foundation checkpoint"
  git -C "$root" tag marker-foundation

  printf '%s\n' 'us1 checkpoint complete' > "$root/specs/prsg-013-reviewability-markers/.process/markers/us1-checkpoint.md"
  git -C "$root" add -A
  git -C "$root" commit -q -m "us1 checkpoint"
  git -C "$root" tag marker-us1

  printf '%s\n' 'us2 part1 checkpoint complete' > "$root/specs/prsg-013-reviewability-markers/.process/markers/us2-part1-checkpoint.md"
  git -C "$root" add -A
  git -C "$root" commit -q -m "us2 part1 checkpoint"
  git -C "$root" tag marker-us2-part1

  git -C "$root" checkout -q main
  git init --bare "$remote" >/dev/null 2>&1
  git -C "$root" remote add origin "$remote"
  git -C "$root" push -u origin main >/dev/null 2>&1
}

write_fake_live_gh() {
  local bin_dir="$1"
  mkdir -p "$bin_dir"
  cat > "$bin_dir/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

log="${FAKE_GH_LOG:?}"
repo="${FAKE_GH_REPO:-$PWD}"

if [ "${1:-}" != "pr" ]; then
  printf 'unsupported gh command\n' >&2
  exit 1
fi

subcommand="${2:-}"
shift 2

case "$subcommand" in
  list)
    printf '[]\n'
    ;;
  create)
    base=""
    head=""
    title=""
    body_file=""
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --base) base="${2:-}"; shift 2 ;;
        --head) head="${2:-}"; shift 2 ;;
        --title) title="${2:-}"; shift 2 ;;
        --body-file) body_file="${2:-}"; shift 2 ;;
        *) shift ;;
      esac
    done
    [ -n "$base" ] && [ -n "$head" ] && [ -n "$body_file" ] || exit 1
    count=0
    if [ -f "$log" ]; then
      count="$(wc -l < "$log" | tr -d ' ')"
    fi
    number=$((900 + count + 1))
    url="https://github.example/pr/$number"
    jq -cn \
      --arg base "$base" \
      --arg head "$head" \
      --arg title "$title" \
      --arg body_file "$body_file" \
      --arg url "$url" \
      --argjson number "$number" \
      '{number:$number,url:$url,state:"OPEN",base:$base,head:$head,title:$title,body_file:$body_file}' >> "$log"
    printf '%s\n' "$url"
    ;;
  view)
    ref="${1:-}"
    [ -n "$ref" ] || exit 1
    record="$(jq -c --arg url "$ref" 'select(.url == $url)' "$log" | tail -1)"
    [ -n "$record" ] || exit 1
    number="$(printf '%s' "$record" | jq -r '.number')"
    url="$(printf '%s' "$record" | jq -r '.url')"
    head="$(printf '%s' "$record" | jq -r '.head')"
    head_sha="$(git -C "$repo" rev-parse "$head")"
    jq -cn \
      --argjson number "$number" \
      --arg url "$url" \
      --arg state "OPEN" \
      --arg headRefOid "$head_sha" \
      '{number:$number,url:$url,state:$state,headRefOid:$headRefOid}'
    ;;
  *)
    printf 'unsupported gh pr command: %s\n' "$subcommand" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "$bin_dir/gh"
}

set_test "live marker emission requires checkpoint SHAs before branch mutation"
live_marker_repo="$SANDBOX/live-marker-repo"
make_marker_persist_repo "$live_marker_repo"
live_marker_state="$live_marker_repo/docs/ai/specs/.process/autopilot-state.json"
live_marker_evidence="$live_marker_repo/specs/prsg-013-reviewability-markers/.process/emission/full-regression.txt"
result=0
run_emission output stderr_output "$SCRIPT" \
  --marker-plan "$valid_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$live_marker_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$live_marker_evidence" \
  --live || result=$?
assert_eq "2" "$result" "exit code"
assert_contains "$stderr_output" "multi-pr-emission.sh: input_error: --live requires checkpoint_sha for slice foundation"

set_test "live marker emission creates marker branches and PRs from checkpoint SHAs"
live_success_repo="$SANDBOX/live-marker-success-repo"
live_success_remote="$SANDBOX/live-marker-success-remote.git"
make_live_marker_success_repo "$live_success_repo" "$live_success_remote"
live_success_state="$live_success_repo/docs/ai/specs/.process/autopilot-state.json"
live_success_evidence="$live_success_repo/specs/prsg-013-reviewability-markers/.process/emission/full-regression.txt"
live_success_prs="$live_success_repo/specs/prsg-013-reviewability-markers/.process/prs.json"
live_success_commands="$SANDBOX/live-marker-success-commands.json"
live_success_marker_plan="$SANDBOX/live-marker-plan-with-shas.json"
live_success_fake_bin="$SANDBOX/live-marker-fake-bin"
live_success_gh_log="$SANDBOX/live-marker-gh-create.jsonl"
write_fake_live_gh "$live_success_fake_bin"
live_base_sha="$(git -C "$live_success_repo" rev-parse main)"
live_foundation_sha="$(git -C "$live_success_repo" rev-parse marker-foundation)"
live_us1_sha="$(git -C "$live_success_repo" rev-parse marker-us1)"
live_us2_sha="$(git -C "$live_success_repo" rev-parse marker-us2-part1)"
jq \
  --arg foundation_sha "$live_foundation_sha" \
  --arg us1_sha "$live_us1_sha" \
  --arg us2_sha "$live_us2_sha" '
    .markers |= map(
      if .id == "foundation" then .implementation_checkpoint.head_sha = $foundation_sha
      elif .id == "us1" then .implementation_checkpoint.head_sha = $us1_sha
      elif .id == "us2-part1" then .implementation_checkpoint.head_sha = $us2_sha
      else . end
    )
  ' "$valid_marker_plan" > "$live_success_marker_plan"

result=0
run_emission output stderr_output env \
  PATH="$live_success_fake_bin:$PATH" \
  FAKE_GH_LOG="$live_success_gh_log" \
  FAKE_GH_REPO="$live_success_repo" \
  "$SCRIPT" \
  --marker-plan "$live_success_marker_plan" \
  --marker-split-result "$marker_split_result" \
  --state "$live_success_state" \
  --feature-branch prsg-013-reviewability-markers \
  --base main \
  --base-sha "$live_base_sha" \
  --full-verification-evidence "$live_success_evidence" \
  --command-log "$live_success_commands" \
  --live || result=$?
assert_eq "0" "$result" "exit code"

set_test "live marker emission reports branch and pull-request mutation"
json_check "$output" \
  "data['status'] == 'persisted' and data['mutation']['branches'] == True and data['mutation']['pull_requests'] == True and data['emission']['mode'] == 'marker' and data['emission']['marker_count'] == 3" \
  "live marker emission should report live branch and PR mutation"

set_test "live marker emission pushes each marker branch to its checkpoint SHA"
remote_foundation_sha="$(git -C "$live_success_remote" rev-parse refs/heads/prsg-013-reviewability-markers/01-foundation)"
remote_us1_sha="$(git -C "$live_success_remote" rev-parse refs/heads/prsg-013-reviewability-markers/02-us1)"
remote_us2_sha="$(git -C "$live_success_remote" rev-parse refs/heads/prsg-013-reviewability-markers/03-us2-part1)"
if [ "$remote_foundation_sha" = "$live_foundation_sha" ] && [ "$remote_us1_sha" = "$live_us1_sha" ] && [ "$remote_us2_sha" = "$live_us2_sha" ]; then
  _pass
else
  _fail "marker branches should point at their checkpoint SHAs"
fi

live_success_gh_json="$(jq -s '.' "$live_success_gh_log" 2>/dev/null || printf '[]')"
set_test "live marker emission creates PRs with marker branch bases"
json_check "$live_success_gh_json" \
  "[r['head'] for r in data] == ['prsg-013-reviewability-markers/01-foundation', 'prsg-013-reviewability-markers/02-us1', 'prsg-013-reviewability-markers/03-us2-part1'] and [r['base'] for r in data] == ['main', 'prsg-013-reviewability-markers/01-foundation', 'prsg-013-reviewability-markers/02-us1']" \
  "live gh create calls should preserve marker branch/base order"

live_success_state_json="$(cat "$live_success_state" 2>/dev/null || true)"
set_test "live marker emission completes state with opened PRs"
json_check "$live_success_state_json" \
  "data['multi_pr_emission']['status'] == 'complete' and data['multi_pr_emission']['next_slice_id'] is None and [s['status'] for s in data['multi_pr_emission']['slices']] == ['pr_opened', 'pr_opened', 'pr_opened'] and [s['head_sha'] for s in data['multi_pr_emission']['slices']] == ['$live_foundation_sha', '$live_us1_sha', '$live_us2_sha']" \
  "live state should complete with checkpoint-backed opened PRs"

live_success_prs_json="$(cat "$live_success_prs" 2>/dev/null || true)"
set_test "live marker emission writes PRS manifest with checkpoint heads"
json_check "$live_success_prs_json" \
  "data['schemaVersion'] == 2 and [r['slice_id'] for r in data['records']] == ['foundation', 'us1', 'us2-part1'] and [r['head_sha'] for r in data['records']] == ['$live_foundation_sha', '$live_us1_sha', '$live_us2_sha'] and [r['pr_number'] for r in data['records']] == [901, 902, 903]" \
  "live PRS manifest should preserve checkpoint head SHAs"

live_success_commands_json="$(cat "$live_success_commands" 2>/dev/null || true)"
set_test "live marker emission records git and gh operations"
json_check "$live_success_commands_json" \
  "len([op for op in data['operations'] if op['action'] == 'git_branch']) == 3 and len([op for op in data['operations'] if op['action'] == 'git_push']) == 3 and len([op for op in data['operations'] if op['action'] == 'gh_pr_create']) == 3" \
  "live command log should record branch, push, and PR create operations"

section "US2 persistence and resume reconciliation"

make_persist_repo() {
  local root="$1"
  mkdir -p \
    "$root/docs/ai/specs/.process" \
    "$root/specs/prsg-009-multi-pr-emission/.process/emission" \
    "$root/specs/prsg-009-multi-pr-emission/.process" \
    "$root/speckit-pro/skills/speckit-autopilot/scripts"
  printf '{}\n' > "$root/docs/ai/specs/.process/autopilot-state.json"
  cat > "$root/specs/prsg-009-multi-pr-emission/SPEC-MOC.md" <<'EOF'
---
structureVersion: 1
spec_id: PRSG-009
---

# PRSG-009 Fixture

<!-- GENERATED:PRS:START (do not edit; regenerated by generate-spec-index.sh) -->
<!-- GENERATED:PRS:END -->
EOF
  cat > "$root/docs/ai/specs/.process/PRSG-009-workflow.md" <<'EOF'
# PRSG-009 Workflow Fixture

## Phase 7: Implement
EOF
  printf '%s\n' 'US2 full regression fixture passed' > "$root/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
}

write_pr_fixture() {
  local target="$1" mode="$2"
  case "$mode" in
    success)
      cat > "$target" <<'EOF'
{
  "existing": [],
  "created": [
    {"slice_id":"foundation","head":"prsg-009-multi-pr-emission/01-foundation","base":"main","number":301,"url":"https://github.example/pr/301","state":"OPEN","head_sha":"sha-foundation"},
    {"slice_id":"us1","head":"prsg-009-multi-pr-emission/02-us1","base":"prsg-009-multi-pr-emission/01-foundation","number":302,"url":"https://github.example/pr/302","state":"OPEN","head_sha":"sha-us1"},
    {"slice_id":"us2","head":"prsg-009-multi-pr-emission/03-us2","base":"prsg-009-multi-pr-emission/02-us1","number":303,"url":"https://github.example/pr/303","state":"OPEN","head_sha":"sha-us2"}
  ]
}
EOF
      ;;
    resume)
      cat > "$target" <<'EOF'
{
  "existing": [
    {"slice_id":"foundation","head":"prsg-009-multi-pr-emission/01-foundation","base":"main","number":301,"url":"https://github.example/pr/301","state":"OPEN","head_sha":"sha-foundation"}
  ],
  "created": [
    {"slice_id":"us1","head":"prsg-009-multi-pr-emission/02-us1","base":"prsg-009-multi-pr-emission/01-foundation","number":302,"url":"https://github.example/pr/302","state":"OPEN","head_sha":"sha-us1"},
    {"slice_id":"us2","head":"prsg-009-multi-pr-emission/03-us2","base":"prsg-009-multi-pr-emission/02-us1","number":303,"url":"https://github.example/pr/303","state":"OPEN","head_sha":"sha-us2"}
  ]
}
EOF
      ;;
    closed)
      cat > "$target" <<'EOF'
{
  "existing": [
    {"slice_id":"foundation","head":"prsg-009-multi-pr-emission/01-foundation","base":"main","number":301,"url":"https://github.example/pr/301","state":"CLOSED","head_sha":"sha-foundation","merged_sha":null}
  ],
  "created": []
}
EOF
      ;;
    create-failure)
      cat > "$target" <<'EOF'
{
  "existing": [],
  "created": [],
  "create_failures": [
    {"slice_id":"foundation","head":"prsg-009-multi-pr-emission/01-foundation","base":"main","exit_status":4,"stderr":"GraphQL unavailable"}
  ]
}
EOF
      ;;
    single-us1)
      cat > "$target" <<'EOF'
{
  "existing": [],
  "created": [
    {"slice_id":"us1","head":"prsg-009-multi-pr-emission/01-us1","base":"main","number":401,"url":"https://github.example/pr/401","state":"OPEN","head_sha":"sha-us1-single"}
  ]
}
EOF
      ;;
  esac
}

persist_repo="$SANDBOX/persist-repo"
make_persist_repo "$persist_repo"
persist_state="$persist_repo/docs/ai/specs/.process/autopilot-state.json"
persist_prs="$persist_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
persist_moc="$persist_repo/specs/prsg-009-multi-pr-emission/SPEC-MOC.md"
persist_workflow="$persist_repo/docs/ai/specs/.process/PRSG-009-workflow.md"
persist_full_evidence="$persist_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
persist_fixture="$SANDBOX/pr-fixture-success.json"
persist_commands="$SANDBOX/pr-commands-success.json"
write_pr_fixture "$persist_fixture" success

set_test "successful emission persists state, PRS, MOC, and workflow"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$persist_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$persist_full_evidence" \
  --pr-fixture "$persist_fixture" \
  --command-log "$persist_commands" || result=$?
assert_eq "0" "$result" "exit code"

persist_state_json="$(cat "$persist_state" 2>/dev/null || true)"
persist_prs_json="$(cat "$persist_prs" 2>/dev/null || true)"
persist_moc_body="$(cat "$persist_moc" 2>/dev/null || true)"
persist_workflow_body="$(cat "$persist_workflow" 2>/dev/null || true)"
persist_commands_json="$(cat "$persist_commands" 2>/dev/null || true)"

set_test "successful emission advances next_slice_id only after all surfaces persist"
json_check "$persist_state_json" \
  "data['multi_pr_emission']['status'] == 'complete' and data['multi_pr_emission']['next_slice_id'] is None and [s['status'] for s in data['multi_pr_emission']['slices']] == ['pr_opened', 'pr_opened', 'pr_opened']" \
  "state should complete only after PRS/MOC/workflow persistence"

set_test "successful emission PRS rows preserve review order and PR numbers"
json_check "$persist_prs_json" \
  "data['schemaVersion'] == 2 and [r['slice_id'] for r in data['records']] == ['foundation', 'us1', 'us2'] and [r['pr_number'] for r in data['records']] == [301, 302, 303]" \
  "PRS manifest should record opened PRs in slice order"

set_test "successful emission regenerates SPEC-MOC PRS table"
assert_contains "$persist_moc_body" "| 1 | foundation | PR#301 | opened | prsg-009-multi-pr-emission/01-foundation | main | sha-foundation |"

set_test "successful emission records workflow evidence"
assert_contains "$persist_workflow_body" "US2 emission evidence"

set_test "successful emission captures explicit gh pr create commands"
json_check "$persist_commands_json" \
  "[op['command'][0:8] for op in data['operations'] if op['action'] == 'gh_pr_create'] == [['gh', 'pr', 'create', '--base', 'main', '--head', 'prsg-009-multi-pr-emission/01-foundation', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-009-multi-pr-emission/01-foundation', '--head', 'prsg-009-multi-pr-emission/02-us1', '--body-file'], ['gh', 'pr', 'create', '--base', 'prsg-009-multi-pr-emission/02-us1', '--head', 'prsg-009-multi-pr-emission/03-us2', '--body-file']]" \
  "persistent mode should preserve explicit PR create command shape"

set_test "successful emission validates each layer packet before gh pr create"
json_check "$persist_commands_json" \
  "data['operations'][1]['action'] == 'validate_pr_packet' and data['operations'][2]['action'] == 'gh_pr_create' and data['operations'][1]['slice_id'] == data['operations'][2]['slice_id'] and data['operations'][4]['action'] == 'validate_pr_packet' and data['operations'][5]['action'] == 'gh_pr_create' and data['operations'][4]['slice_id'] == data['operations'][5]['slice_id'] and data['operations'][8]['action'] == 'validate_pr_packet' and data['operations'][9]['action'] == 'gh_pr_create' and data['operations'][8]['slice_id'] == data['operations'][9]['slice_id']" \
  "persistent layer emission should validate the packet immediately before PR creation"

set_test "successful emission leaves no sibling temp files"
temp_files="$(find "$persist_repo" -name '.tmp.*' -o -name '.spec-index.*' 2>/dev/null | LC_ALL=C sort || true)"
assert_eq "" "$temp_files" "same-directory temp writes should be cleaned up"

resume_repo="$SANDBOX/resume-repo"
make_persist_repo "$resume_repo"
resume_state="$resume_repo/docs/ai/specs/.process/autopilot-state.json"
resume_prs="$resume_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
resume_moc="$resume_repo/specs/prsg-009-multi-pr-emission/SPEC-MOC.md"
resume_workflow="$resume_repo/docs/ai/specs/.process/PRSG-009-workflow.md"
resume_full_evidence="$resume_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
resume_fixture="$SANDBOX/pr-fixture-resume.json"
resume_commands="$SANDBOX/pr-commands-resume.json"
write_pr_fixture "$resume_fixture" resume

set_test "resume reconciles existing PR by expected head and base"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$resume_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$resume_full_evidence" \
  --pr-fixture "$resume_fixture" \
  --command-log "$resume_commands" || result=$?
assert_eq "0" "$result" "exit code"

resume_state_json="$(cat "$resume_state" 2>/dev/null || true)"
resume_prs_json="$(cat "$resume_prs" 2>/dev/null || true)"
resume_commands_json="$(cat "$resume_commands" 2>/dev/null || true)"
resume_moc_body="$(cat "$resume_moc" 2>/dev/null || true)"
resume_workflow_body="$(cat "$resume_workflow" 2>/dev/null || true)"

set_test "resume state backfills existing open PR and completes"
json_check "$resume_state_json" \
  "data['multi_pr_emission']['status'] == 'complete' and data['multi_pr_emission']['slices'][0]['pr']['number'] == 301 and data['multi_pr_emission']['slices'][0]['status'] == 'pr_opened'" \
  "resume should backfill existing open PR metadata"

set_test "resume does not duplicate existing foundation PR"
json_check "$resume_commands_json" \
  "[op['slice_id'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['us1', 'us2']" \
  "resume should not run gh pr create for the reconciled foundation PR"

set_test "resume backfills stale PRS manifest, MOC, and workflow"
json_check "$resume_prs_json" \
  "len(data['records']) == 3 and data['records'][0]['pr_number'] == 301" \
  "resume should write missing PRS rows"
assert_contains "$resume_moc_body" "PR#301"
assert_contains "$resume_workflow_body" "Reconciled existing PR#301"

closed_repo="$SANDBOX/closed-repo"
make_persist_repo "$closed_repo"
closed_state="$closed_repo/docs/ai/specs/.process/autopilot-state.json"
closed_full_evidence="$closed_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
closed_fixture="$SANDBOX/pr-fixture-closed.json"
closed_commands="$SANDBOX/pr-commands-closed.json"
write_pr_fixture "$closed_fixture" closed

set_test "closed unmerged PR blocks without duplicate creation"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$closed_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$closed_full_evidence" \
  --pr-fixture "$closed_fixture" \
  --command-log "$closed_commands" || result=$?
assert_eq "2" "$result" "exit code"

closed_state_json="$(cat "$closed_state" 2>/dev/null || true)"
closed_commands_json="$(cat "$closed_commands" 2>/dev/null || true)"
set_test "closed unmerged PR keeps next_slice_id on blocked slice"
json_check "$closed_state_json" \
  "data['multi_pr_emission']['status'] == 'blocked' and data['multi_pr_emission']['next_slice_id'] == 'foundation' and data['multi_pr_emission']['slices'][0]['status'] == 'closed'" \
  "closed PR should require operator action before retry"

set_test "closed unmerged PR does not create a replacement PR"
json_check "$closed_commands_json" \
  "[op for op in data['operations'] if op['action'] == 'gh_pr_create'] == []" \
  "closed PR reconciliation must not duplicate PRs"
assert_contains "$stderr_output" "closed PR blocks slice foundation"

fail_repo="$SANDBOX/create-fail-repo"
make_persist_repo "$fail_repo"
fail_state="$fail_repo/docs/ai/specs/.process/autopilot-state.json"
fail_prs="$fail_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
fail_full_evidence="$fail_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
fail_fixture="$SANDBOX/pr-fixture-create-failure.json"
fail_commands="$SANDBOX/pr-commands-create-failure.json"
write_pr_fixture "$fail_fixture" create-failure

set_test "gh pr create failure blocks with recoverable state"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$fail_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$fail_full_evidence" \
  --pr-fixture "$fail_fixture" \
  --command-log "$fail_commands" || result=$?
assert_eq "2" "$result" "exit code"

fail_state_json="$(cat "$fail_state" 2>/dev/null || true)"
fail_commands_json="$(cat "$fail_commands" 2>/dev/null || true)"
set_test "gh pr create failure records last_error and does not advance"
json_check "$fail_state_json" \
  "data['multi_pr_emission']['status'] == 'blocked' and data['multi_pr_emission']['next_slice_id'] == 'foundation' and data['multi_pr_emission']['slices'][0]['last_error']['phase'] == 'gh_pr_create'" \
  "create failure should block at the failed slice"

set_test "gh pr create failure writes no PRS row"
assert_file_not_exists "$fail_prs"

set_test "gh pr create failure captures attempted command"
json_check "$fail_commands_json" \
  "[op['slice_id'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['foundation']" \
  "failed PR create should leave command evidence"
assert_contains "$stderr_output" "gh pr create failed for slice foundation"

persist_fail_repo="$SANDBOX/persist-fail-repo"
make_persist_repo "$persist_fail_repo"
persist_fail_state="$persist_fail_repo/docs/ai/specs/.process/autopilot-state.json"
persist_fail_prs="$persist_fail_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
persist_fail_full_evidence="$persist_fail_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
persist_fail_fixture="$SANDBOX/pr-fixture-persist-failure.json"
persist_fail_commands="$SANDBOX/pr-commands-persist-failure.json"
write_pr_fixture "$persist_fail_fixture" success
rm -f "$persist_fail_prs"
mkdir -p "$persist_fail_prs"

set_test "post-PR PRS persistence failure blocks without advancing next_slice_id"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$persist_fail_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$persist_fail_full_evidence" \
  --pr-fixture "$persist_fail_fixture" \
  --command-log "$persist_fail_commands" || result=$?
assert_eq "2" "$result" "exit code"

persist_fail_state_json="$(cat "$persist_fail_state" 2>/dev/null || true)"
set_test "post-PR persistence failure keeps opened PR recoverable"
json_check "$persist_fail_state_json" \
  "data['multi_pr_emission']['status'] == 'blocked' and data['multi_pr_emission']['next_slice_id'] == 'foundation' and data['multi_pr_emission']['slices'][0]['status'] == 'pr_opened' and data['multi_pr_emission']['slices'][0]['pr']['number'] == 301 and data['multi_pr_emission']['slices'][0]['last_error']['phase'] == 'prs_persist'" \
  "post-PR persistence failure should not lose opened PR metadata or advance"
assert_contains "$stderr_output" "persistence failed after PR opened for slice foundation"

set_test "split partial-failure resume fixture exists"
assert_file_exists "$REPO_ROOT/tests/speckit-pro/layer4-scripts/fixtures/pr-packet/split-partial-failure-state.json"

section "US3 scoped verification evidence"

set_test "candidate slice packet maps PRSG-008 tests to SCRIPT_UNIT scoped verification"
json_check "$foundation_packet_json" \
  "data['scoped_verification']['commands'][0]['command'] == 'bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh' and data['scoped_verification']['commands'][0]['gate_type'] == 'SCRIPT_UNIT' and data['scoped_verification']['commands'][0]['required'] == True and data['scoped_verification']['commands'][0]['exit_status'] == 0 and data['scoped_verification']['commands'][0]['evidence_path'] == 'specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log'" \
  "candidate slice packet should map declared PRSG-008 tests to scoped verification evidence"

set_test "candidate state records scoped verification command mapping"
json_check "$state_json" \
  "data['multi_pr_emission']['slices'][0]['scoped_verification']['commands'][0]['gate_type'] == 'SCRIPT_UNIT' and data['multi_pr_emission']['slices'][0]['declared_scoped_tests'] == ['bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh']" \
  "candidate state should include scoped verification records for reviewers and resume"

no_scope_repo="$SANDBOX/no-scope-repo"
make_persist_repo "$no_scope_repo"
no_scope_plan="$SANDBOX/no-scoped-plan.json"
jq '.increments[0].tests = []' "$single_slice_plan" > "$no_scope_plan"
no_scope_state="$no_scope_repo/docs/ai/specs/.process/autopilot-state.json"
no_scope_full_evidence="$no_scope_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
no_scope_fixture="$SANDBOX/pr-fixture-no-scope.json"
no_scope_commands="$SANDBOX/pr-commands-no-scope.json"
write_pr_fixture "$no_scope_fixture" single-us1

set_test "slice with no scoped tests emits required no_scoped_tests evidence"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$no_scope_plan" \
  --state "$no_scope_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$no_scope_full_evidence" \
  --pr-fixture "$no_scope_fixture" \
  --command-log "$no_scope_commands" || result=$?
assert_eq "0" "$result" "exit code"

no_scope_state_json="$(cat "$no_scope_state" 2>/dev/null || true)"
no_scope_packet_json="$(cat "$no_scope_repo/specs/prsg-009-multi-pr-emission/.process/emission/us1/slice-packet.json" 2>/dev/null || true)"
no_scope_evidence="$no_scope_repo/specs/prsg-009-multi-pr-emission/.process/emission/us1/no_scoped_tests.txt"

set_test "no_scoped_tests evidence file exists"
assert_file_exists "$no_scope_evidence"

set_test "no_scoped_tests evidence explains no-op rationale"
assert_contains "$(cat "$no_scope_evidence" 2>/dev/null || true)" "No declared scoped tests or applicable project command"

set_test "no_scoped_tests packet entry is required reviewer evidence"
json_check "$no_scope_packet_json" \
  "len(data['scoped_verification']['commands']) == 1 and data['scoped_verification']['commands'][0]['gate_type'] == 'no_scoped_tests' and data['scoped_verification']['commands'][0]['command'] == '<none>' and data['scoped_verification']['commands'][0]['required'] == True and data['scoped_verification']['commands'][0]['exit_status'] == 0 and data['scoped_verification']['commands'][0]['evidence_path'] == 'specs/prsg-009-multi-pr-emission/.process/emission/us1/no_scoped_tests.txt'" \
  "no scoped tests should still produce a required scoped-verification packet entry"

set_test "no_scoped_tests state entry persists with opened PR"
json_check "$no_scope_state_json" \
  "data['multi_pr_emission']['status'] == 'complete' and data['multi_pr_emission']['slices'][0]['status'] == 'pr_opened' and data['multi_pr_emission']['slices'][0]['scoped_verification']['commands'][0]['gate_type'] == 'no_scoped_tests'" \
  "no scoped tests should be persisted as evidence, not silently skipped"

scoped_fail_repo="$SANDBOX/scoped-fail-repo"
make_persist_repo "$scoped_fail_repo"
scoped_fail_state="$scoped_fail_repo/docs/ai/specs/.process/autopilot-state.json"
scoped_fail_prs="$scoped_fail_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
scoped_fail_workflow="$scoped_fail_repo/docs/ai/specs/.process/PRSG-009-workflow.md"
scoped_fail_full_evidence="$scoped_fail_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
scoped_fail_fixture="$SANDBOX/pr-fixture-scoped-fail.json"
scoped_fail_commands="$SANDBOX/pr-commands-scoped-fail.json"
scoped_verification_fixture="$SANDBOX/scoped-verification-us1-fail.json"
write_pr_fixture "$scoped_fail_fixture" success
cat > "$scoped_verification_fixture" <<'EOF'
{
  "slices": {
    "foundation": {
      "commands": [
        {
          "command": "bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh",
          "gate_type": "SCRIPT_UNIT",
          "reason": "Synthetic scoped pass",
          "required": true,
          "evidence_path": "specs/prsg-009-multi-pr-emission/.process/emission/foundation/layer4.log",
          "exit_status": 0,
          "started_at": "2026-06-10T00:00:00Z",
          "finished_at": "2026-06-10T00:00:01Z"
        }
      ]
    },
    "us1": {
      "commands": [
        {
          "command": "bash tests/speckit-pro/layer4-scripts/test-multi-pr-emission.sh",
          "gate_type": "SCRIPT_UNIT",
          "reason": "Synthetic scoped failure",
          "required": true,
          "evidence_path": "specs/prsg-009-multi-pr-emission/.process/emission/us1/layer4.log",
          "exit_status": 1,
          "started_at": "2026-06-10T00:00:00Z",
          "finished_at": "2026-06-10T00:00:01Z",
          "stdout_tail": "41/61 passed",
          "stderr_tail": "synthetic scoped failure"
        }
      ]
    }
  }
}
EOF

set_test "later scoped verification failure stops before failed slice PR creation"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$valid_plan" \
  --state "$scoped_fail_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$scoped_fail_full_evidence" \
  --pr-fixture "$scoped_fail_fixture" \
  --command-log "$scoped_fail_commands" \
  --scoped-verification-fixture "$scoped_verification_fixture" || result=$?
assert_eq "2" "$result" "exit code"

scoped_fail_state_json="$(cat "$scoped_fail_state" 2>/dev/null || true)"
scoped_fail_prs_json="$(cat "$scoped_fail_prs" 2>/dev/null || true)"
scoped_fail_commands_json="$(cat "$scoped_fail_commands" 2>/dev/null || true)"
scoped_fail_workflow_body="$(cat "$scoped_fail_workflow" 2>/dev/null || true)"
scoped_fail_evidence="$scoped_fail_repo/specs/prsg-009-multi-pr-emission/.process/emission/us1/layer4.log"

set_test "failed scoped verification records failed_slice and keeps next_slice_id on us1"
json_check "$scoped_fail_state_json" \
  "data['multi_pr_emission']['status'] == 'blocked' and data['multi_pr_emission']['next_slice_id'] == 'us1' and data['multi_pr_emission']['failed_slice']['slice_id'] == 'us1' and data['multi_pr_emission']['failed_slice']['phase'] == 'scoped_verification' and data['multi_pr_emission']['failed_slice']['stderr_tail'] == 'synthetic scoped failure'" \
  "failed scoped verification should block at the failed slice with durable failure evidence"

set_test "later scoped verification failure preserves earlier opened PR"
json_check "$scoped_fail_state_json" \
  "data['multi_pr_emission']['slices'][0]['slice_id'] == 'foundation' and data['multi_pr_emission']['slices'][0]['status'] == 'pr_opened' and data['multi_pr_emission']['slices'][0]['pr']['number'] == 301 and data['multi_pr_emission']['slices'][1]['slice_id'] == 'us1' and data['multi_pr_emission']['slices'][1]['status'] == 'failed' and 'pr' not in data['multi_pr_emission']['slices'][1]" \
  "later failures should not rewind earlier persisted PRs or create failed-slice PRs"

set_test "failed scoped verification leaves PRS manifest with earlier slice only"
json_check "$scoped_fail_prs_json" \
  "[r['slice_id'] for r in data['records']] == ['foundation'] and data['records'][0]['status'] == 'opened'" \
  "PRS should retain earlier opened slice rows only"

set_test "failed scoped verification records failure evidence file"
assert_file_exists "$scoped_fail_evidence"
assert_contains "$(cat "$scoped_fail_evidence" 2>/dev/null || true)" "synthetic scoped failure"

set_test "failed scoped verification does not capture gh pr create for failed slice"
json_check "$scoped_fail_commands_json" \
  "[op['slice_id'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['foundation']" \
  "failed scoped verification must stop before gh pr create for us1"

set_test "failed scoped verification workflow evidence names blocked next_slice_id"
assert_contains "$scoped_fail_workflow_body" 'Failed scoped verification for `us1`'
assert_contains "$scoped_fail_workflow_body" 'next_slice_id: `us1`'
assert_contains "$stderr_output" "multi-pr-emission.sh: blocked: scoped verification failed for slice us1"

invalid_packet_repo="$SANDBOX/invalid-packet-repo"
make_persist_repo "$invalid_packet_repo"
invalid_packet_plan="$SANDBOX/invalid-packet-plan.json"
invalid_packet_state="$invalid_packet_repo/docs/ai/specs/.process/autopilot-state.json"
invalid_packet_prs="$invalid_packet_repo/specs/prsg-009-multi-pr-emission/.process/prs.json"
invalid_packet_workflow="$invalid_packet_repo/docs/ai/specs/.process/PRSG-009-workflow.md"
invalid_packet_full_evidence="$invalid_packet_repo/specs/prsg-009-multi-pr-emission/.process/emission/full-regression.txt"
invalid_packet_fixture="$SANDBOX/pr-fixture-invalid-packet.json"
invalid_packet_commands="$SANDBOX/pr-commands-invalid-packet.json"
write_pr_fixture "$invalid_packet_fixture" success
jq '.increments[1].files = []' "$valid_plan" > "$invalid_packet_plan"

set_test "invalid split packet blocks before that slice PR creation"
result=0
run_emission output stderr_output "$SCRIPT" \
  --layer-plan "$invalid_packet_plan" \
  --state "$invalid_packet_state" \
  --feature-branch prsg-009-multi-pr-emission \
  --base main \
  --base-sha 0123456789abcdef \
  --full-verification-evidence "$invalid_packet_full_evidence" \
  --pr-fixture "$invalid_packet_fixture" \
  --command-log "$invalid_packet_commands" || result=$?
assert_eq "2" "$result" "exit code"

invalid_packet_state_json="$(cat "$invalid_packet_state" 2>/dev/null || true)"
invalid_packet_prs_json="$(cat "$invalid_packet_prs" 2>/dev/null || true)"
invalid_packet_commands_json="$(cat "$invalid_packet_commands" 2>/dev/null || true)"
invalid_packet_workflow_body="$(cat "$invalid_packet_workflow" 2>/dev/null || true)"

set_test "invalid split packet preserves earlier PR evidence"
json_check "$invalid_packet_state_json" \
  "data['multi_pr_emission']['status'] == 'blocked' and data['multi_pr_emission']['next_slice_id'] == 'us1' and data['multi_pr_emission']['slices'][0]['status'] == 'pr_opened' and data['multi_pr_emission']['slices'][0]['pr']['number'] == 301 and data['multi_pr_emission']['slices'][1]['status'] == 'failed' and data['multi_pr_emission']['slices'][1]['last_error']['phase'] == 'pr_packet_validation' and 'pr' not in data['multi_pr_emission']['slices'][1]" \
  "invalid packet validation should block at us1 without losing the foundation PR"

set_test "invalid split packet leaves PRS manifest with earlier slice only"
json_check "$invalid_packet_prs_json" \
  "[r['slice_id'] for r in data['records']] == ['foundation'] and data['records'][0]['status'] == 'opened'" \
  "PRS should retain earlier opened slice rows only after packet validation failure"

set_test "invalid split packet does not duplicate earlier PRs or create failed-slice PR"
json_check "$invalid_packet_commands_json" \
  "[op['slice_id'] for op in data['operations'] if op['action'] == 'gh_pr_create'] == ['foundation'] and [op['slice_id'] for op in data['operations'] if op['action'] == 'validate_pr_packet'] == ['foundation', 'us1']" \
  "packet validation failure should validate failed slice but skip its gh pr create"

set_test "invalid split packet workflow event is recorded"
assert_contains "$invalid_packet_workflow_body" "speckit-pro-pr-packet-validation:event-id=us1"

set_test "invalid split packet stderr identifies validation block"
assert_contains "$stderr_output" "validate-pr-packet.sh failed for slice us1"

test_summary

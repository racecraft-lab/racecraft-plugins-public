#!/usr/bin/env bash
# validate-pr-checks-sentinel.sh — Verifies the validate-plugins sentinel job
# exists in .github/workflows/pr-checks.yml with the correct configuration.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"

# Navigate two levels up from tests/layer1-structural to speckit-pro, then one
# more level to the repo root where .github/workflows/ lives.
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
WORKFLOW_FILE="$REPO_ROOT/.github/workflows/pr-checks.yml"

section "pr-checks.yml — Sentinel Job Existence"

set_test "pr-checks.yml exists"
assert_file_exists "$WORKFLOW_FILE"

CONTENT=$(cat "$WORKFLOW_FILE")

set_test "validate-plugins job is defined"
assert_contains "$CONTENT" "validate-plugins:"

set_test "validate-plugins has name: validate-plugins"
assert_contains "$CONTENT" "name: validate-plugins"

section "pr-checks.yml — PR Workflow Contract"

set_test "title validation checks out repository history"
if [[ "$CONTENT" == *"uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10"* \
  && "$CONTENT" == *"fetch-depth: 0"* ]]; then
  _pass
else
  _fail "expected validate-pr-title to checkout repository history before inspecting changed files"
fi

set_test "title validation uses shared workflow contract validator"
assert_contains "$CONTENT" "validate-pr-workflow-contract.sh"

set_test "title validation supplies changed-file evidence"
if [[ "$CONTENT" == *"git diff --name-only"* \
  && "$CONTENT" == *"--changed-files .git/pr-changed-files.txt"* ]]; then
  _pass
else
  _fail "expected title validation to pass changed-file evidence to the contract validator"
fi

section "pr-checks.yml — Workflow Validation"

set_test "workflow validation job is defined"
assert_contains "$CONTENT" "validate-workflows:"

set_test "workflow validation installs pinned actionlint"
if [[ "$CONTENT" == *'ACTIONLINT_VERSION: "1.7.12"'* \
  && "$CONTENT" == *'ACTIONLINT_SHA256: "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"'* \
  && "$CONTENT" == *"https://github.com/rhysd/actionlint/releases/download/v"* \
  && "$CONTENT" == *"sha256sum -c"* ]]; then
  _pass
else
  _fail "expected validate-workflows to install actionlint from a pinned release with checksum verification"
fi

set_test "workflow validation runs actionlint over all workflows"
if [[ "$CONTENT" == *'"${RUNNER_TEMP}/actionlint" .github/workflows/*.yml'* ]]; then
  _pass
else
  _fail "expected validate-workflows to run actionlint over all GitHub workflow YAML files"
fi

set_test "deploy-docs workflow changes trigger structural tests"
if [[ "$CONTENT" == *".github/workflows/(pr-checks|release|deploy-docs)"* ]]; then
  _pass
else
  _fail "expected workflow detector to include deploy-docs.yml so deploy workflow changes run plugin structural tests"
fi

section "pr-checks.yml — Release PR Dispatch"

set_test "workflow_dispatch trigger is defined"
assert_contains "$CONTENT" "workflow_dispatch:"

set_test "dispatched PR checks identify the PR number"
if [[ "$CONTENT" == *'run-name: "PR Checks #'* \
  && "$CONTENT" == *"inputs.pr_number"* ]]; then
  _pass
else
  _fail "expected workflow_dispatch runs to include the PR number in run-name"
fi

set_test "workflow_dispatch accepts PR check inputs"
if [[ "$CONTENT" == *"pr_number:"* \
  && "$CONTENT" == *"pr_title:"* \
  && "$CONTENT" == *"base_ref:"* ]]; then
  _pass
else
  _fail "expected workflow_dispatch inputs for pr_number, pr_title, and base_ref"
fi

set_test "detect supports dispatched release PR checks"
if [[ "$CONTENT" == *"github.event_name == 'workflow_dispatch' || github.event.pull_request.draft == false"* \
  && "$CONTENT" == *"github.event_name == 'pull_request' && github.base_ref || inputs.base_ref"* ]]; then
  _pass
else
  _fail "expected detect job to use workflow_dispatch base_ref input"
fi

set_test "title validation supports dispatched release PR checks"
if [[ "$CONTENT" == *"github.event_name == 'pull_request' && github.event.pull_request.title || inputs.pr_title"* ]]; then
  _pass
else
  _fail "expected title validation to use workflow_dispatch pr_title input"
fi

section "pr-checks.yml — Sentinel Job Dependencies"

set_test "sentinel depends on detect job"
assert_contains "$CONTENT" "needs: [detect, test]"

set_test "sentinel runs if: always()"
assert_contains "$CONTENT" "if: always()"

set_test "sentinel has permissions: {}"
assert_contains "$CONTENT" "permissions: {}"

section "pr-checks.yml — Sentinel Job Logic"

set_test "sentinel checks detect_result for failure"
assert_contains "$CONTENT" 'detect_result'

set_test "sentinel checks test_result for success or skipped"
assert_contains "$CONTENT" 'test_result'

set_test "sentinel exits 0 on success or skipped"
assert_contains "$CONTENT" '"success" || "$test_result" == "skipped"'

set_test "sentinel exits 1 on detect failure"
assert_contains "$CONTENT" '"failure"'

set_test "sentinel exits 1 on detect cancellation"
assert_contains "$CONTENT" '"cancelled"'

section "GitHub Workflows — YAML Syntax"

set_test "all GitHub workflow files are valid YAML"
yaml_failures=()
for workflow in "$REPO_ROOT"/.github/workflows/*.yml; do
  if python3 -c "import yaml, sys; yaml.safe_load(sys.stdin)" < "$workflow" 2>/dev/null; then
    continue
  elif ruby -e "require 'yaml'; YAML.load_file(ARGV.fetch(0))" "$workflow" >/dev/null 2>&1; then
    continue
  fi
  yaml_failures+=("$(basename "$workflow")")
done

if [ "${#yaml_failures[@]}" -eq 0 ]; then
  _pass
else
  _fail "GitHub workflow YAML syntax validation failed for: ${yaml_failures[*]}"
fi

test_summary

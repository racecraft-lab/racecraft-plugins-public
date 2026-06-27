#!/usr/bin/env bash
# validate-uat-runbook.sh - Reject skeleton-quality UAT runbooks before PR creation.

set -euo pipefail

usage() {
  printf 'Usage: validate-uat-runbook.sh <uat-runbook-path>\n' >&2
}

fail() {
  local rule="$1" message="$2"
  printf 'validate-uat-runbook.sh: validation_failure: %s: %s\n' "$rule" "$message" >&2
  exit 1
}

if [ "$#" -ne 1 ]; then
  usage
  exit 2
fi

RUNBOOK="$1"

if [ ! -r "$RUNBOOK" ] || [ ! -f "$RUNBOOK" ]; then
  fail "uat.missing" "runbook is missing or unreadable: $RUNBOOK"
fi

if grep -Fq 'autopilot did not pass PROJECT_COMMANDS' "$RUNBOOK"; then
  fail "uat.env_setup" "Env Setup still contains unknown PROJECT_COMMANDS placeholders"
fi

if grep -Fq '| Command | Value |' "$RUNBOOK"; then
  fail "uat.env_setup" "Env Setup still uses the skeleton command table instead of plain reviewer instructions"
fi

if grep -Fq 'Walk this story end to end and confirm the observable behavior the spec promises.' "$RUNBOOK"; then
  fail "uat.per_story" "Per-Story Acceptance Tests still contain skeleton placeholder text"
fi

if grep -Fq 'see the Per-Story Acceptance Tests block above' "$RUNBOOK"; then
  fail "uat.fr_matrix" "FR Coverage Matrix still contains the circular skeleton placeholder"
fi

if grep -Fq 'No UAT runbook was generated for this feature' "$RUNBOOK"; then
  fail "uat.missing" "PR body still contains the absent-runbook fallback"
fi

if grep -Eq '<a[[:space:]][^>]*id=' "$RUNBOOK"; then
  fail "uat.html_anchor" "runbook still contains raw HTML anchor markup"
fi

if grep -Fq '<set on PR open>' "$RUNBOOK" || grep -Fq '| PR | **PR:**' "$RUNBOOK"; then
  fail "uat.pr_placeholder" "runbook still contains the old PR placeholder"
fi

printf 'validate-uat-runbook.sh: ok: %s\n' "$RUNBOOK"

#!/usr/bin/env bash
# validate-pr-workflow-contract.sh - Validate PR title/split workflow metadata.

set -euo pipefail

SCRIPT_NAME="validate-pr-workflow-contract.sh"

usage() {
  printf 'Usage: validate-pr-workflow-contract.sh --title <title> [--changed-files <path>] [--repo-root <path>]\n' >&2
}

input_error() {
  printf '%s: input_error: %s\n' "$SCRIPT_NAME" "$1" >&2
  exit 2
}

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TITLE=""
CHANGED_FILES=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --title)
      [ "$#" -ge 2 ] || input_error "missing value for --title"
      TITLE="$2"
      shift 2
      ;;
    --changed-files)
      [ "$#" -ge 2 ] || input_error "missing value for --changed-files"
      CHANGED_FILES="$2"
      shift 2
      ;;
    --repo-root)
      [ "$#" -ge 2 ] || input_error "missing value for --repo-root"
      REPO_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      input_error "unknown argument $1"
      ;;
  esac
done

[ -n "$TITLE" ] || input_error "missing required option --title"
[ -d "$REPO_ROOT" ] || input_error "repo root not found: $REPO_ROOT"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

failures_file="$tmp_dir/failures.jsonl"
scopes_file="$tmp_dir/scopes.txt"
changed_file="$tmp_dir/changed-files.txt"
: > "$failures_file"
: > "$scopes_file"

add_failure() {
  local rule="$1" message="$2" evidence="$3"
  jq -cn \
    --arg rule "$rule" \
    --arg message "$message" \
    --arg evidence "$evidence" \
    '{rule:$rule,message:$message,evidence:$evidence}' >> "$failures_file"
}

spec_scope_from_feature_slug() {
  local slug="$1" suffix
  if [[ "$slug" =~ ^[Pp][Rr][Ss][Gg]-([0-9]+)(-|$) ]]; then
    printf 'PRSG-%s\n' "${BASH_REMATCH[1]}"
  elif [[ "$slug" =~ ^[Ss][Pp][Ee][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    suffix="${BASH_REMATCH[1]^^}"
    printf 'SPEC-%s\n' "$suffix"
  elif [[ "$slug" =~ ^[Dd][Oo][Cc]-([0-9A-Za-z]+)(-|$) ]]; then
    suffix="${BASH_REMATCH[1]^^}"
    printf 'DOC-%s\n' "$suffix"
  fi
}

if [ -n "$CHANGED_FILES" ]; then
  [ -r "$CHANGED_FILES" ] || input_error "changed-files list not readable: $CHANGED_FILES"
  cp "$CHANGED_FILES" "$changed_file"
else
  if ! git -C "$REPO_ROOT" rev-parse --verify origin/main >/dev/null 2>&1; then
    input_error "missing --changed-files and origin/main is unavailable"
  fi
  git -C "$REPO_ROOT" diff --name-only origin/main...HEAD > "$changed_file"
fi

title_type=""
title_scope=""
title_regex='^(feat|fix|chore|docs|refactor|test)(\(([^)]+)\))?!?:[[:space:]]+.+$'
if [[ "$TITLE" =~ $title_regex ]]; then
  title_type="${BASH_REMATCH[1]}"
  title_scope="${BASH_REMATCH[3]:-}"
else
  add_failure "title.format" "PR title must follow Conventional Commits format." "$TITLE"
fi

while IFS= read -r changed_path; do
  case "$changed_path" in
    specs/*/*)
      feature_slug="${changed_path#specs/}"
      feature_slug="${feature_slug%%/*}"
      scope="$(spec_scope_from_feature_slug "$feature_slug")"
      [ -n "$scope" ] && printf '%s\n' "$scope" >> "$scopes_file"
      ;;
  esac
done < "$changed_file"

sort -u "$scopes_file" -o "$scopes_file"
scope_count="$(sed '/^[[:space:]]*$/d' "$scopes_file" | wc -l | tr -d ' ')"

if [ "$scope_count" = "1" ]; then
  expected_scope="$(cat "$scopes_file")"
  if [ -n "$title_scope" ] && [ "$title_scope" != "$expected_scope" ]; then
    add_failure "title.spec_scope" \
      "Spec implementation PR titles must use the active spec id as the Conventional Commit scope." \
      "expected=$expected_scope actual=$title_scope"
  elif [ -z "$title_scope" ]; then
    add_failure "title.spec_scope" \
      "Spec implementation PR titles must include the active spec id as the Conventional Commit scope." \
      "expected=$expected_scope actual=empty"
  fi

  if [[ "$expected_scope" == DOC-* ]] && [ "$title_type" != "docs" ]; then
    add_failure "title.doc_type" \
      "Documentation spec implementation PR titles must use docs(<DOC-ID>):." \
      "expected=docs actual=${title_type:-empty}"
  fi
elif [ "$scope_count" -gt 1 ]; then
  if ! grep -Fxq "$title_scope" "$scopes_file"; then
    add_failure "title.spec_scope" \
      "PR title scope must match one changed spec id when multiple spec directories are present." \
      "title_scope=${title_scope:-empty} changed_scopes=$(paste -sd, "$scopes_file")"
  fi
fi

if grep -Eq '^specs/[^/]+/\.process/.*/commands\.candidate\.json$|^specs/[^/]+/\.process/emission/candidate/commands\.candidate\.json$' "$changed_file"; then
  command -v jq >/dev/null 2>&1 || input_error "jq is required for split-candidate validation"
fi

while IFS= read -r changed_path; do
  case "$changed_path" in
    specs/*/.process/*/commands.candidate.json|specs/*/.process/emission/candidate/commands.candidate.json)
      candidate_path="$REPO_ROOT/$changed_path"
      [ -f "$candidate_path" ] || continue
      pr_count="$(jq '[.operations[]? | select(.action == "gh_pr_create")] | length' "$candidate_path" 2>/dev/null || printf '0')"
      if [ "$pr_count" -gt 1 ]; then
        add_failure "split.aggregate_candidate" \
          "PR includes multi-PR split candidate commands; open the planned slice PRs instead of one aggregate PR." \
          "$changed_path pr_count=$pr_count"
      fi
      ;;
  esac
done < "$changed_file"

if grep -Eq '^specs/[^/]+/.*/final-marker-split-result\.json$|^specs/[^/]+/\.process/.*/final-marker-split-result\.json$' "$changed_file"; then
  command -v jq >/dev/null 2>&1 || input_error "jq is required for marker-split validation"
fi

while IFS= read -r changed_path; do
  case "$changed_path" in
    specs/*/*final-marker-split-result.json)
      split_path="$REPO_ROOT/$changed_path"
      [ -f "$split_path" ] || continue
      split_route="$(jq -r '.emission.route // .outcome // empty' "$split_path" 2>/dev/null || true)"
      marker_count="$(jq -r '(.emission.markers // []) | length' "$split_path" 2>/dev/null || printf '0')"
      if [ "$split_route" = "marker_split" ] && [ "$marker_count" -gt 1 ]; then
        add_failure "split.marker_result" \
          "PR includes final marker_split evidence for multiple PRs; use multi-pr-emission.sh instead of an aggregate PR." \
          "$changed_path marker_count=$marker_count"
      fi
      ;;
  esac
done < "$changed_file"

if [ -s "$failures_file" ]; then
  failures_json="$(jq -s . "$failures_file")"
  printf '%s\n' "$failures_json" | jq -c \
    --arg title "$TITLE" \
    '{script:"validate-pr-workflow-contract",status:"failed",title:$title,failures:.}'
  first_rule="$(jq -r -s '.[0].rule' "$failures_file")"
  printf '%s: validation_failure: %s\n' "$SCRIPT_NAME" "$first_rule" >&2
  exit 1
fi

jq -cn --arg title "$TITLE" '{script:"validate-pr-workflow-contract",status:"passed",title:$title}'

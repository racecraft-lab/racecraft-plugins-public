#!/usr/bin/env bash
# validate-capability-resolution.sh — Layer 1 target-resolution check (FR-004).
#
# For each in-scope agent's directive reference, extract the in-source,
# repo-root-relative path token VERBATIM and assert it resolves under BOTH
# built trees:
#     dist/claude/<path-token>   AND   dist/codex/<path-token>
#
# Resolution is PREFIX RE-ROOTING (research Decision 3): the builder copies
# source under `dist/<runtime>/` preserving the `speckit-pro/**` sub-path, so
# the same token that appears in source must resolve under each built tree.
# This is NOT a runtime-relative `../references/…` walk — no active agent uses
# one. The check FAILS when a path is correct in source but absent in either
# built tree; it MUST NOT pass on source-tree presence alone (FR-004).
#
# Covers the same in-scope set as the pointer-coverage check, across both
# Claude `speckit-pro/agents/*.md` and Codex `speckit-pro/codex-agents/*.toml`
# (FR-009 parity). Fail-closed on an empty agent glob, a token that cannot be
# extracted, or a missing `dist/**` target (FR-012).
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

AGENTS_DIR="$PLUGIN_ROOT/agents"
CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

DIST_CLAUDE="$REPO_ROOT/dist/claude"
DIST_CODEX="$REPO_ROOT/dist/codex"

DIRECTIVE_MARKER="capability-discovery.md"
GROUNDING_MARKER="grounding.md"

# Extract the repo-root-relative path token verbatim. The token is the
# `speckit-pro/…/capability-discovery.md` substring, cited the same way by both
# runtimes (backtick-wrapped in Claude `.md`, bare in the Codex TOML
# "Capability discovery equivalent: mirrors …" line). A bracket character class
# (not a non-portable `\b`) bounds the path so trailing prose/punctuation is
# excluded.
PATH_TOKEN_RE='speckit-pro/[A-Za-z0-9._/-]*capability-discovery\.md'

# The companion grounding-contract token, cited the same way alongside the
# directive token. Resolved under both built trees identically.
GROUNDING_TOKEN_RE='speckit-pro/[A-Za-z0-9._/-]*grounding\.md'

# Out-of-scope EXCLUSION set — mirrors validate-capability-pointer.sh. Excluded
# agents carry no directive reference, so there is no token to resolve for them.
CC_EXCLUSIONS=(
  "consensus-synthesizer"
  "gate-validator"
  "phase-executor"
)
CODEX_EXCLUSIONS=(
  "autopilot-fast-helper"
  "phase-executor"
)

is_in_list() {
  local needle="$1"; shift
  local item
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

is_excluded() {
  local runtime="$1" name="$2"
  if [ "$runtime" = "claude" ]; then
    is_in_list "$name" "${CC_EXCLUSIONS[@]}"
  else
    is_in_list "$name" "${CODEX_EXCLUSIONS[@]}"
  fi
}

# Accumulate the unique set of path tokens found across all in-scope agents,
# so resolution is asserted once per distinct token (and we can fail-closed if
# the whole inventory yielded nothing to resolve).
declare -a FOUND_TOKENS=()

token_seen() {
  local needle="$1" t
  for t in "${FOUND_TOKENS[@]:-}"; do
    [ "$t" = "$needle" ] && return 0
  done
  return 1
}

# collect_runtime <runtime-label> <agents-dir> <glob-ext>
# Iterates active agents, extracting the directive path token from each
# in-scope referencing agent into FOUND_TOKENS.
collect_runtime() {
  local runtime="$1" dir="$2" ext="$3"

  set_test "${runtime}: agents directory exists ($dir)"
  if [ ! -d "$dir" ]; then
    _fail "agents directory missing: $dir"
    return
  fi
  _pass

  local files=()
  local f
  for f in "$dir"/*."$ext"; do
    [ -f "$f" ] && files+=("$f")
  done

  set_test "${runtime}: active-agent glob matched at least one agent"
  if [ "${#files[@]}" -eq 0 ]; then
    _fail "no active agents found under $dir/*.$ext (empty glob — refusing to pass vacuously)"
    return
  fi
  _pass

  local agent_name tok found_dir found_gr
  for f in "${files[@]}"; do
    agent_name=$(basename "$f" ".$ext")
    is_excluded "$runtime" "$agent_name" && continue

    # In-scope agent: it MUST carry an extractable directive token. If a
    # referencing agent's token cannot be extracted, fail-closed rather than
    # silently skip it (FR-012).
    if ! grep -q "$DIRECTIVE_MARKER" "$f"; then
      # Pointer coverage is the pointer check's job; here we only resolve
      # tokens that exist. A missing reference is reported by
      # validate-capability-pointer.sh, so skip without a token.
      continue
    fi

    # Collect EVERY unique directive token in the file, not just the first.
    # A file with one valid reference and one stale/broken reference must not
    # pass on the strength of the valid one — every token is resolved below.
    found_dir=0
    while read -r tok; do
      [ -z "$tok" ] && continue
      found_dir=1
      token_seen "$tok" || FOUND_TOKENS+=("$tok")
    done < <(grep -oE "$PATH_TOKEN_RE" "$f" | sort -u)
    set_test "${runtime}: extracted directive path token(s) from in-scope agent '${agent_name}'"
    if [ "$found_dir" -eq 1 ]; then
      _pass
    else
      _fail "agent references ${DIRECTIVE_MARKER} but no repo-root-relative path token matched ${PATH_TOKEN_RE} in $f"
    fi

    # Companion grounding token(s) (same in-scope set). Also collect ALL unique
    # matches; the pointer check enforces presence, so here we resolve every
    # token an agent that references grounding actually carries.
    if grep -q "$GROUNDING_MARKER" "$f"; then
      found_gr=0
      while read -r tok; do
        [ -z "$tok" ] && continue
        found_gr=1
        token_seen "$tok" || FOUND_TOKENS+=("$tok")
      done < <(grep -oE "$GROUNDING_TOKEN_RE" "$f" | sort -u)
      set_test "${runtime}: extracted grounding path token(s) from in-scope agent '${agent_name}'"
      if [ "$found_gr" -eq 1 ]; then
        _pass
      else
        _fail "agent references ${GROUNDING_MARKER} but no repo-root-relative path token matched ${GROUNDING_TOKEN_RE} in $f"
      fi
    fi
  done
}

section "Collect directive path tokens — Claude (speckit-pro/agents/*.md)"
collect_runtime "claude" "$AGENTS_DIR" "md"

section "Collect directive path tokens — Codex (speckit-pro/codex-agents/*.toml)"
collect_runtime "codex" "$CODEX_AGENTS_DIR" "toml"

# Fail-closed: the inventory must have yielded at least one path token to
# resolve. Zero tokens means the resolution check would otherwise pass while
# verifying nothing (FR-012).
section "Target Resolution — re-root each token under dist/claude AND dist/codex"

set_test "at least one directive path token was collected from the inventory"
if [ "${#FOUND_TOKENS[@]}" -eq 0 ]; then
  _fail "no directive path tokens collected — refusing to report resolution success on zero work"
  test_summary
  exit $?
fi
_pass

# Fail-closed: both built trees must exist before we resolve anything under them.
set_test "built Claude payload tree exists ($DIST_CLAUDE)"
if [ -d "$DIST_CLAUDE" ]; then _pass; else _fail "missing built tree: $DIST_CLAUDE"; fi

set_test "built Codex payload tree exists ($DIST_CODEX)"
if [ -d "$DIST_CODEX" ]; then _pass; else _fail "missing built tree: $DIST_CODEX"; fi

# For each unique token, assert prefix re-rooting resolves in BOTH built trees.
for tok in "${FOUND_TOKENS[@]}"; do
  set_test "resolves under dist/claude: ${tok}"
  assert_file_exists "$DIST_CLAUDE/$tok" \
    "directive path correct in source but absent in built Claude tree (dist/claude/$tok)"

  set_test "resolves under dist/codex: ${tok}"
  assert_file_exists "$DIST_CODEX/$tok" \
    "directive path correct in source but absent in built Codex tree (dist/codex/$tok)"
done

test_summary

#!/usr/bin/env bash
# validate-capability-pointer.sh — Layer 1 pointer-coverage check (FR-003).
#
# Proves every capability-dependent active agent references the shared
# capability-discovery directive (`capability-discovery.md`) by literal path,
# OR appears in the enumerated approved-equivalent allowlist. Agents that
# perform no capability-dependent work are listed in an enumerated exclusion
# set (one reason each) so "uncovered" cannot be confused with "out of scope".
#
# Partition (the load-bearing rule):
#   - EXCLUSION set     → the ONLY agents allowed to omit the pointer.
#   - approved-equiv    → literal enumerated allowlist (currently EMPTY,
#                         since every in-scope agent references directly).
#   - everything else   → IN-SCOPE BY DEFAULT. The 6 known in-scope agents
#                         AND any future/unenumerated agent must reference
#                         `capability-discovery.md` (or be allowlisted), else
#                         FAIL naming the uncovered agent.
#
# The exclusion set and allowlist are literal enumerations (not heuristics) so
# they stay auditable. Neither may be widened merely to silence an in-scope
# agent that drops the pointer (FR-012). Covers both Claude `speckit-pro/agents/*.md`
# and Codex `speckit-pro/codex-agents/*.toml` (FR-009 parity).
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"

AGENTS_DIR="$PLUGIN_ROOT/agents"
CODEX_AGENTS_DIR="$PLUGIN_ROOT/codex-agents"

# The literal path token an in-scope agent must reference.
DIRECTIVE_MARKER="capability-discovery.md"

# ---------------------------------------------------------------------------
# Out-of-scope EXCLUSION set — agents that perform NO capability-dependent work
# (terminal validation, synthesis-only, or fast-path workers that gather no
# external context). These are the ONLY agents allowed to omit the pointer.
# One-line reason each (FR-003). MUST NOT be widened to silence an in-scope
# agent that drops the pointer.
# ---------------------------------------------------------------------------

# Claude exclusions (speckit-pro/agents/*.md):
CC_EXCLUSIONS=(
  "consensus-synthesizer"   # synthesis-only: aggregates prior agent output, gathers no external context
  "gate-validator"          # terminal validation: checks gate state, performs no capability-dependent research
  "phase-executor"          # orchestration shell: dispatches sub-agents, gathers no context itself
  "spec-context-analyst"    # reads in-repo spec artifacts only; no external capability-dependent work
  "uat-runbook-author"      # authors a runbook from existing artifacts; no external research
)

# Codex exclusions (speckit-pro/codex-agents/*.toml):
CODEX_EXCLUSIONS=(
  "autopilot-fast-helper"   # fast-path helper: deterministic assists, gathers no external context
  "phase-executor"          # orchestration shell: dispatches sub-agents, gathers no context itself
  "spec-context-analyst"    # reads in-repo spec artifacts only; no external capability-dependent work
  "uat-runbook-author"      # authors a runbook from existing artifacts; no external research
)

# ---------------------------------------------------------------------------
# Approved-equivalent allowlist — agents that legitimately carry a machine-
# checkable runtime-specific equivalent INSTEAD of the literal path reference.
# Literal enumeration; currently EMPTY because every in-scope agent references
# `capability-discovery.md` directly. An entry here is the EXPLICIT, auditable
# escape hatch — it MUST NOT be added merely to turn a red check green.
# Format (when non-empty): "<runtime>:<agent-name>".
# ---------------------------------------------------------------------------
APPROVED_EQUIVALENTS=(
  # (empty) — no in-scope agent uses an approved equivalent today.
)

is_in_list() {
  local needle="$1"; shift
  local item
  for item in "$@"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

# is_excluded <runtime> <agent-name>
is_excluded() {
  local runtime="$1" name="$2"
  if [ "$runtime" = "claude" ]; then
    is_in_list "$name" "${CC_EXCLUSIONS[@]}"
  else
    is_in_list "$name" "${CODEX_EXCLUSIONS[@]}"
  fi
}

# is_approved_equivalent <runtime> <agent-name>
# Guarded against an empty array under `set -u`.
is_approved_equivalent() {
  local runtime="$1" name="$2"
  [ "${#APPROVED_EQUIVALENTS[@]}" -eq 0 ] && return 1
  is_in_list "${runtime}:${name}" "${APPROVED_EQUIVALENTS[@]}"
}

# check_runtime <runtime-label> <agents-dir> <glob-ext>
# Iterates every active agent file for a runtime and applies the partition.
check_runtime() {
  local runtime="$1" dir="$2" ext="$3"

  # Fail-closed: the agents directory must exist (FR-012).
  set_test "${runtime}: agents directory exists ($dir)"
  if [ ! -d "$dir" ]; then
    _fail "agents directory missing: $dir"
    return
  fi
  _pass

  # Fail-closed: the active-agent glob must match at least one file, so the
  # check cannot pass vacuously by examining nothing (FR-012).
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

  local agent_name
  for f in "${files[@]}"; do
    agent_name=$(basename "$f" ".$ext")

    # Out-of-scope: explicitly excluded, with a recorded reason. Not required
    # to carry the pointer; nothing to assert.
    if is_excluded "$runtime" "$agent_name"; then
      continue
    fi

    # In-scope by default (the 6 known referencing agents PLUS any future
    # agent not in the exclusion set). It must EITHER reference the directive
    # by literal path OR appear in the approved-equivalent allowlist.
    set_test "${runtime}: in-scope agent '${agent_name}' references ${DIRECTIVE_MARKER} (or approved equivalent)"
    if grep -q "$DIRECTIVE_MARKER" "$f"; then
      _pass
    elif is_approved_equivalent "$runtime" "$agent_name"; then
      _pass
    else
      _fail "uncovered in-scope agent: ${runtime} '${agent_name}' references neither ${DIRECTIVE_MARKER} nor an approved equivalent (add the pointer, or record it in the exclusion set with a reason — do NOT widen the allowlist to silence it)"
    fi
  done
}

section "Pointer Coverage — Claude agents (speckit-pro/agents/*.md)"
check_runtime "claude" "$AGENTS_DIR" "md"

section "Pointer Coverage — Codex agents (speckit-pro/codex-agents/*.toml)"
check_runtime "codex" "$CODEX_AGENTS_DIR" "toml"

test_summary

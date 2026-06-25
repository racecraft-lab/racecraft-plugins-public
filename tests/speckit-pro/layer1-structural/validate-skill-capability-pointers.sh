#!/usr/bin/env bash
# validate-skill-capability-pointers.sh — Layer 1 skill pointer-coverage check.
#
# capability-discovery.md declares Universal Scope: the directive binds "all
# subagents, the orchestrator, and the user-invocable skills." The agent-side
# pointer/resolution checks (validate-capability-pointer.sh /
# validate-capability-resolution.sh) only cover speckit-pro/agents and
# codex-agents, so without this check a user-invocable SKILL could silently drop
# its capability-discovery / grounding pointers while the universal-scope claim
# still reads as enforced.
#
# This check covers the skill surface for BOTH runtimes:
#   - speckit-pro/skills/<name>/SKILL.md          (Claude)
#   - speckit-pro/codex-skills/<name>/SKILL.md    (Codex)
#
# Partition (mirrors the agent checks): every skill is IN SCOPE BY DEFAULT and
# must reference BOTH capability-discovery.md and grounding.md by literal path,
# and both tokens must resolve under dist/claude AND dist/codex. The only skills
# allowed to omit the pointers are the enumerated, mechanical EXCLUSIONS below
# (one reason each). The exclusion set MUST NOT be widened merely to silence an
# in-scope skill that drops a pointer.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../../../speckit-pro" && pwd)"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

CLAUDE_SKILLS_DIR="$PLUGIN_ROOT/skills"
CODEX_SKILLS_DIR="$PLUGIN_ROOT/codex-skills"
DIST_CLAUDE="$REPO_ROOT/dist/claude"
DIST_CODEX="$REPO_ROOT/dist/codex"

DIRECTIVE_MARKER="capability-discovery.md"
GROUNDING_MARKER="grounding.md"
PATH_TOKEN_RE='speckit-pro/[A-Za-z0-9._/-]*capability-discovery\.md'
GROUNDING_TOKEN_RE='speckit-pro/[A-Za-z0-9._/-]*grounding\.md'

# Mechanical / non-research skills that legitimately omit the directive: they
# install/upgrade tooling, report repo state from direct file reads, or clean up
# merged-spec residue — none enumerate installed capabilities or assert external
# facts that need grounding. Applies to both runtimes (Codex also ships `install`).
EXCLUSIONS=(
  "speckit-install"          # installs the SpecKit CLI; mechanical, no external research
  "install"                  # Codex install skill; mechanical
  "speckit-upgrade"          # backup-and-restore upgrade; mechanical
  "speckit-status"           # reports roadmap state from direct repo-file reads; no open discovery
  "speckit-archive-cleanup"  # archives merged-spec residue; mechanical
)

# The orchestrator HOSTS capability-discovery.md and grounding.md in its own
# references/ directory and links them with relative paths (./references/...),
# so it carries no repo-root path token to resolve. It is NOT excluded — its
# pointer PRESENCE is still enforced (so it cannot silently drop the references);
# only the repo-root token resolution is skipped for it, because the files it
# points at are the canonical sources and are already resolved under both dist
# trees by validate-capability-resolution.sh.
HOST_SKILL="speckit-autopilot"

is_excluded() {
  local needle="$1" item
  for item in "${EXCLUSIONS[@]}"; do
    [ "$item" = "$needle" ] && return 0
  done
  return 1
}

declare -a FOUND_TOKENS=()
token_seen() {
  local needle="$1" t
  for t in "${FOUND_TOKENS[@]:-}"; do
    [ "$t" = "$needle" ] && return 0
  done
  return 1
}

# collect_marker <runtime> <skill> <SKILL.md> <marker> <token-re>
# Asserts the file references <marker> and extracts EVERY unique path token for
# it (not just the first — a stale second reference must still be resolved).
collect_marker() {
  local runtime="$1" skill="$2" file="$3" marker="$4" token_re="$5"
  set_test "${runtime} skill '${skill}' references ${marker}"
  if ! grep -q "$marker" "$file"; then
    _fail "in-scope skill '${skill}' (${runtime}) does not reference ${marker} (add the pointer, or record it in EXCLUSIONS with a reason — do NOT widen EXCLUSIONS to silence it)"
    return
  fi
  _pass
  local tok found=0
  while read -r tok; do
    [ -z "$tok" ] && continue
    found=1
    token_seen "$tok" || FOUND_TOKENS+=("$tok")
  done < <(grep -oE "$token_re" "$file" | sort -u)
  set_test "${runtime} skill '${skill}' ${marker} reference yields a repo-root-relative path token"
  if [ "$found" -eq 1 ]; then _pass; else
    _fail "skill references ${marker} but no token matched ${token_re} in $file"
  fi
}

check_runtime() {
  local runtime="$1" dir="$2"

  set_test "${runtime}: skills directory exists ($dir)"
  if [ ! -d "$dir" ]; then _fail "skills directory missing: $dir"; return; fi
  _pass

  local skill_dirs=() d
  for d in "$dir"/*/; do
    [ -f "${d}SKILL.md" ] && skill_dirs+=("$d")
  done

  set_test "${runtime}: at least one skill with a SKILL.md was found"
  if [ "${#skill_dirs[@]}" -eq 0 ]; then
    _fail "no skills found under $dir/*/SKILL.md (empty glob — refusing to pass vacuously)"
    return
  fi
  _pass

  local skill
  for d in "${skill_dirs[@]}"; do
    skill=$(basename "$d")
    is_excluded "$skill" && continue
    if [ "$skill" = "$HOST_SKILL" ]; then
      # Presence-only: enforce that the host still references both markers (so it
      # cannot silently drop them); skip repo-root token resolution since it
      # links them relatively.
      set_test "${runtime} host skill '${skill}' references ${DIRECTIVE_MARKER}"
      if grep -q "$DIRECTIVE_MARKER" "${d}SKILL.md"; then _pass; else
        _fail "host skill '${skill}' (${runtime}) dropped its ${DIRECTIVE_MARKER} reference"
      fi
      set_test "${runtime} host skill '${skill}' references ${GROUNDING_MARKER}"
      if grep -q "$GROUNDING_MARKER" "${d}SKILL.md"; then _pass; else
        _fail "host skill '${skill}' (${runtime}) dropped its ${GROUNDING_MARKER} reference"
      fi
      continue
    fi
    collect_marker "$runtime" "$skill" "${d}SKILL.md" "$DIRECTIVE_MARKER" "$PATH_TOKEN_RE"
    collect_marker "$runtime" "$skill" "${d}SKILL.md" "$GROUNDING_MARKER" "$GROUNDING_TOKEN_RE"
  done
}

section "Skill Pointer Coverage — Claude (speckit-pro/skills/*/SKILL.md)"
check_runtime "claude" "$CLAUDE_SKILLS_DIR"

section "Skill Pointer Coverage — Codex (speckit-pro/codex-skills/*/SKILL.md)"
check_runtime "codex" "$CODEX_SKILLS_DIR"

section "Skill Pointer Resolution — re-root each token under dist/claude AND dist/codex"

set_test "at least one skill directive/grounding token was collected"
if [ "${#FOUND_TOKENS[@]}" -eq 0 ]; then
  _fail "no skill path tokens collected — refusing to report resolution success on zero work"
  test_summary
  exit $?
fi
_pass

set_test "built Claude payload tree exists ($DIST_CLAUDE)"
if [ -d "$DIST_CLAUDE" ]; then _pass; else _fail "missing built tree: $DIST_CLAUDE"; fi
set_test "built Codex payload tree exists ($DIST_CODEX)"
if [ -d "$DIST_CODEX" ]; then _pass; else _fail "missing built tree: $DIST_CODEX"; fi

for tok in "${FOUND_TOKENS[@]}"; do
  set_test "resolves under dist/claude: ${tok}"
  assert_file_exists "$DIST_CLAUDE/$tok" \
    "skill reference correct in source but absent in built Claude tree (dist/claude/$tok)"
  set_test "resolves under dist/codex: ${tok}"
  assert_file_exists "$DIST_CODEX/$tok" \
    "skill reference correct in source but absent in built Codex tree (dist/codex/$tok)"
done

test_summary

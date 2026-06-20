#!/usr/bin/env bash
# validate-payload-completeness.sh — Layer 1 body-completeness check (FR-008).
#
# The Claude payload builder (`scripts/build-plugin-payloads.sh`) strips the
# `## Codex Skill-Selection Guard` section from each built Claude `SKILL.md`.
# A regression in that strip once dropped the ENTIRE body of 8 of 10 skills,
# shipping empty installs. This check guards against any built Claude SKILL.md
# being truncated relative to its source minus the guard section.
#
# For every built Claude `dist/claude/speckit-pro/skills/<name>/SKILL.md`, find
# its source `speckit-pro/skills/<name>/SKILL.md` and assert BOTH:
#
#   (1) Structural anchor — the LAST level-2 `## ` heading present in the SOURCE
#       (other than the guard heading) is present in the dist SKILL.md. If the
#       body were truncated to EOF, that trailing heading would be missing.
#
#   (2) Per-skill length tolerance — the dist body line count is within a small
#       slack of (source line count − that skill's guard-section line count).
#       The guard section is computed PER SKILL with the SAME heading-to-next-
#       `## `/EOF boundary the fixed `strip_codex_guard` uses — NEVER a single
#       fixed line-count constant shared across skills (FR-008), so the check and
#       the builder cannot disagree on what "the guard section" is.
#
# Scope: `dist/claude/**` only — Codex does not strip the guard (the Codex
# variant is the guard's fallback target). Fail-closed (FR-012) on an empty
# Claude skills glob, a missing source/built SKILL.md, or a read error.
set -euo pipefail

source "$(dirname "$0")/../lib/assertions.sh"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

SRC_SKILLS_DIR="$REPO_ROOT/speckit-pro/skills"
DIST_CLAUDE_SKILLS_DIR="$REPO_ROOT/dist/claude/speckit-pro/skills"

GUARD_HEADING="## Codex Skill-Selection Guard"

# Line slack: the only intended source→built difference is the stripped guard
# section, which this check accounts for exactly via the per-skill guard count.
# A few residual blank lines around the stripped section are tolerated; a real
# body truncation drops hundreds of lines and is caught well outside this band.
LINE_SLACK=5

# guard_section_lines <skill-file>
# Count lines belonging to the Codex guard section using the SAME boundary as
# the fixed strip_codex_guard: from the `## Codex Skill-Selection Guard` heading
# (inclusive), consume up to (not including) the next level-2 `## ` heading, or
# EOF. A level-2 heading starts with "## " (a "### " sub-heading does NOT — it is
# part of the guard section). Prints the integer line count (0 if no guard
# heading is present — that SKILL.md is left untouched by the builder).
guard_section_lines() {
  local file="$1"
  awk -v heading="$GUARD_HEADING" '
    BEGIN { in_guard = 0; count = 0 }
    {
      if (in_guard == 0) {
        if ($0 == heading) { in_guard = 1; count = 1 }
      } else {
        # A new level-2 section ends the guard; "### " is not level-2.
        if (index($0, "## ") == 1) { in_guard = 0 }
        else { count++ }
      }
    }
    END { print count }
  ' "$file"
}

# last_non_guard_heading <skill-file>
# Print the text of the LAST level-2 `## ` heading in the file, excluding the
# guard heading. Empty if the file has no non-guard level-2 heading.
last_non_guard_heading() {
  local file="$1"
  awk -v heading="$GUARD_HEADING" '
    (index($0, "## ") == 1) && (index($0, "### ") != 1) && ($0 != heading) { last = $0 }
    END { if (last != "") print last }
  ' "$file"
}

section "Body completeness — built Claude skills retain full bodies (dist/claude)"

# Fail-closed: the built Claude skills directory must exist before we glob it.
set_test "built Claude skills directory exists ($DIST_CLAUDE_SKILLS_DIR)"
if [ ! -d "$DIST_CLAUDE_SKILLS_DIR" ]; then
  _fail "built Claude skills directory missing: $DIST_CLAUDE_SKILLS_DIR (run scripts/build-plugin-payloads.sh)"
  test_summary
  exit $?
fi
_pass

# Collect the built Claude SKILL.md set.
dist_skills=()
for f in "$DIST_CLAUDE_SKILLS_DIR"/*/SKILL.md; do
  [ -f "$f" ] && dist_skills+=("$f")
done

# Fail-closed: an empty glob means zero work — refuse to pass vacuously (FR-012).
set_test "built Claude skills glob matched at least one SKILL.md"
if [ "${#dist_skills[@]}" -eq 0 ]; then
  _fail "no built Claude SKILL.md found under $DIST_CLAUDE_SKILLS_DIR/*/SKILL.md (empty glob — refusing to pass vacuously)"
  test_summary
  exit $?
fi
_pass

for dist_file in "${dist_skills[@]}"; do
  skill_name=$(basename "$(dirname "$dist_file")")
  src_file="$SRC_SKILLS_DIR/$skill_name/SKILL.md"

  # Fail-closed: every built skill MUST have a readable source counterpart.
  set_test "[$skill_name] source SKILL.md exists and is readable ($src_file)"
  if [ ! -f "$src_file" ] || [ ! -r "$src_file" ]; then
    _fail "built skill '$skill_name' has no readable source SKILL.md at $src_file"
    continue
  fi
  _pass

  set_test "[$skill_name] built SKILL.md is readable ($dist_file)"
  if [ ! -r "$dist_file" ]; then
    _fail "built skill '$skill_name' SKILL.md is not readable at $dist_file"
    continue
  fi
  _pass

  # (1) Structural anchor: the last non-guard level-2 heading in SOURCE must be
  #     present in the built body. Its absence means strip-to-EOF dropped the
  #     trailing real content.
  anchor=$(last_non_guard_heading "$src_file")
  set_test "[$skill_name] source has a non-guard level-2 heading to anchor on"
  if [ -z "$anchor" ]; then
    _fail "source SKILL.md for '$skill_name' has no non-guard '## ' heading — cannot anchor completeness"
    continue
  fi
  _pass

  dist_body=$(cat "$dist_file")
  set_test "[$skill_name] last non-guard source heading survives in built body: '$anchor'"
  assert_contains "$dist_body" "$anchor" \
    "built '$skill_name' SKILL.md is missing the last non-guard source heading ('$anchor') — body truncated"

  # (2) Per-skill length tolerance: built body within LINE_SLACK of
  #     (source lines − this skill's guard-section lines).
  src_lines=$(wc -l < "$src_file")
  dist_lines=$(wc -l < "$dist_file")
  guard_lines=$(guard_section_lines "$src_file")
  expected=$((src_lines - guard_lines))
  diff=$((dist_lines - expected))
  [ "$diff" -lt 0 ] && diff=$(( -diff ))

  set_test "[$skill_name] built body length within tolerance of source-minus-guard (dist=$dist_lines, expected≈$expected, guard=$guard_lines)"
  if [ "$diff" -le "$LINE_SLACK" ]; then
    _pass
  else
    _fail "built '$skill_name' SKILL.md has $dist_lines lines; expected ≈$expected (source $src_lines − guard $guard_lines), off by $diff (> $LINE_SLACK) — likely truncated"
  fi
done

test_summary

#!/usr/bin/env bash
# validate-moc-orphan.sh — Version-gated orphan lint for MOC markers.
#
# For each version-gated `SPEC-MOC.md` (structureVersion bare-integer >= 1):
#   - orphan rule (FR-009/FR-010/FR-016): `up:` MUST be present, non-empty, and a
#     well-formed relative `[]()` link. A `[[wikilink]]` is NOT well-formed here.
#     Does NOT resolve the target — that is the stale-index lint's job.
#   - spec_id join (FR-019): `spec_id` MUST be present, non-empty, and
#     namespace-match the containing directory under the ID-normalization grammar.
#
# The `up:` requirement is scoped to MOC files ONLY (filename exactly
# `SPEC-MOC.md`); non-MOC docs (spec.md / plan.md / tasks.md / contracts/**) are
# never required to carry `up:`. `.process/**` is exempt.
#
# Exempt -> SKIP (never a violation): no marker, no/unreadable fence,
# no/malformed/<1 structureVersion. The gate decision is made BEFORE any body
# read (exempt-before-content, FR-023), so legacy specs can never red-fail.
#
# Exit codes (3-way enum, FR-020/FR-024):
#   0 = clean (no violations among checkable specs, incl. zero gated)
#   1 = one or more content violations in a gated spec (path + rule -> stdout)
#   2 = internal/operational error (trapped) -> stderr, never conflated with 1
#
# Scan roots default to the two real trees (docs/ai/specs/, specs/); an optional
# positional scan-root arg overrides them (FR-015 — runnable in any consuming
# project; the Layer-4 exit-code driver is the second caller). When invoked with
# NO arg, the script also runs its committed-fixture self-tests.
set -euo pipefail

LIB_DIR="$(cd "$(dirname "$0")/../lib" && pwd)"
# shellcheck source=../lib/assertions.sh
source "$LIB_DIR/assertions.sh"
# shellcheck source=../lib/moc-id-normalize.sh
source "$LIB_DIR/moc-id-normalize.sh"
# shellcheck source=../lib/moc-frontmatter.sh
source "$LIB_DIR/moc-frontmatter.sh"

# layer1-structural -> tests -> speckit-pro -> repo root.
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# Gate literal — KEEP IN SYNC with the scaffold template's stamped
# `structureVersion: 1` and moc-frontmatter.sh's gate. No shared version file.
# (The actual integer test lives in moc_is_gated; this comment marks the
# duplication intentionally per the lint-behavior contract.)
GATE_VERSION=1

# ---------------------------------------------------------------------------
# Side-effect-free predicates (pure booleans; no printing, no exit). Safe to
# call inside assert_exit_code and under set -e when guarded by the caller.
# ---------------------------------------------------------------------------

# moc_up_well_formed <marker-file>
# Exit 0 iff `up:` is present, non-empty, and a well-formed relative `[]()`
# link. A `[[wikilink]]` form is NOT well-formed -> exit 1. Exit 1 if absent
# or empty. Does NOT resolve the target.
moc_up_well_formed() {
  local file="$1" up
  up="$(moc_frontmatter_field "$file" up)" || return 1   # absent -> violation
  [ -n "$up" ] || return 1                                # empty  -> violation
  # Reject the wikilink form outright (ill-formed for orphan).
  case "$up" in
    *'[['*) return 1 ;;
  esac
  # Require a well-formed inline link: `[text](target)` somewhere in the value.
  case "$up" in
    *'['*']('*')'*) return 0 ;;
    *) return 1 ;;
  esac
}

# moc_specid_matches_dir <marker-file> <dir-name>
# Exit 0 iff `spec_id` is present, non-empty, and namespace-matches <dir-name>
# under the ID-normalization grammar. Absent/empty spec_id -> exit 1.
moc_specid_matches_dir() {
  local file="$1" dir_name="$2" spec_id
  spec_id="$(moc_frontmatter_field "$file" spec_id)" || return 1  # absent
  [ -n "$spec_id" ] || return 1                                    # empty
  moc_id_match "$spec_id" "$dir_name"
}

# ---------------------------------------------------------------------------
# Scan: evaluate the gated content rules over a scan root. RETURNS (never
# exits). Prints "path + which rule failed" to stdout on each violation.
# Returns 0 when clean, 1 when at least one violation was found.
# ---------------------------------------------------------------------------

# scan_root <root-dir>
# For each immediate child spec directory under <root-dir>, gate on its
# SPEC-MOC.md (exempt-before-content) and apply the orphan + spec_id rules to
# gated markers only. A missing or empty root is SKIPPED (not an error).
scan_root() {
  local root="$1" rc=0 spec_dir marker dir_name
  [ -d "$root" ] || return 0   # missing root -> skip (FR-022)

  for spec_dir in "$root"/*/; do
    [ -d "$spec_dir" ] || continue           # empty root -> glob stays literal
    case "$spec_dir" in
      */.process/*) continue ;;              # .process/** exempt
    esac
    marker="${spec_dir}SPEC-MOC.md"

    # Exempt-before-content (FR-023): gate decision uses ONLY the marker's
    # version field; no body read happens before this.
    if ! moc_is_gated "$marker"; then
      continue                               # no/unreadable/malformed marker -> SKIP
    fi

    dir_name="$(basename "$spec_dir")"

    # Orphan rule (MOC files only — the marker is the only SPEC-MOC.md here).
    if ! moc_up_well_formed "$marker"; then
      printf 'VIOLATION [orphan]: %s — up: missing, empty, or ill-formed (not a well-formed relative [](...) link)\n' "$marker"
      rc=1
    fi

    # spec_id join rule.
    if ! moc_specid_matches_dir "$marker" "$dir_name"; then
      printf 'VIOLATION [spec_id]: %s — spec_id absent/empty or does not namespace-match directory "%s"\n' "$marker" "$dir_name"
      rc=1
    fi
  done

  return "$rc"
}

# ---------------------------------------------------------------------------
# Internal-error trap (FR-020): any UNEXPECTED set -e failure maps to exit 2 on
# stderr — distinct from a content violation (exit 1 on stdout). Disarmed
# before the deliberate final exit so a clean/violation exit is never remapped.
# ---------------------------------------------------------------------------
_on_err() {
  local ec=$?
  printf 'ERROR: validate-moc-orphan.sh: internal failure (exit %d)\n' "$ec" >&2
  trap - ERR EXIT
  exit 2
}
trap _on_err ERR

# ---------------------------------------------------------------------------
# Mode A: explicit scan-root arg -> scan only that root, exit with its result.
# (This is the path the next group's Layer-4 driver exercises.)
#
# KNOWN GAP (handoff to T020): scan_root is called here on the left of `||`,
# which suppresses `set -e` for its entire body — so the ERR trap is inert
# INSIDE scan_root. An internal failure there (e.g. a broken basename) is
# currently surfaced as exit 1, not the contract's exit 2. T020 (Layer-4
# exit-code driver) pins and finalizes the exit-2/stderr half of FR-020/FR-024;
# the fix is to refactor scan_root to accumulate violations in a global counter,
# return 0, and call it BARE so the ERR trap stays live and maps internal
# failures -> 2. This group verifies only exit 0/1 + the stdout path+rule half.
# ---------------------------------------------------------------------------
if [ "$#" -ge 1 ]; then
  rc=0
  scan_root "$1" || rc=$?
  trap - ERR EXIT
  exit "$rc"
fi

# ---------------------------------------------------------------------------
# Mode B (no arg): committed-fixture self-tests + real-tree scan.
# Negative fixtures asserted as VIOLATIONs are PASSES of the assertion (they do
# NOT pollute FAIL_COUNT), so the lint stays GREEN inside the Layer-1 list while
# also scanning the real trees.
# ---------------------------------------------------------------------------
FIX="$(cd "$(dirname "$0")" && pwd)/fixtures/moc"

section "MOC orphan lint — up: well-formedness predicate (T011, FR-009/FR-010)"

set_test "valid relative up: passes"
assert_exit_code 0 moc_up_well_formed "$FIX/orphan/orphan-valid/SPEC-MOC.md"

set_test "missing up: is a violation"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-missing-up/SPEC-MOC.md"

set_test "empty up: is a violation"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-empty-up/SPEC-MOC.md"

set_test "wikilink up: is a violation (ill-formed for orphan)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-wikilink-up/SPEC-MOC.md"

set_test "non-MOC docs in a gated spec are not required to carry up: (scan clean)"
assert_exit_code 0 scan_root "$FIX/scan-clean"

section "MOC orphan lint — version gate / parsing (T013, FR-013/FR-021/FR-023)"

set_test "no structureVersion -> SKIP (not gated)"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-no-version/SPEC-MOC.md"

set_test "structureVersion 0 (< 1) -> SKIP"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-version-zero/SPEC-MOC.md"

set_test "quoted \"1\" -> SKIP (non-bare-integer)"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-version-quoted/SPEC-MOC.md"

set_test "decimal 1.0 -> SKIP (non-bare-integer)"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-version-decimal/SPEC-MOC.md"

set_test "non-numeric text -> SKIP (non-bare-integer)"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-version-text/SPEC-MOC.md"

set_test "no --- fence -> SKIP (unparseable frontmatter)"
assert_exit_code 1 moc_is_gated "$FIX/gate/gate-no-fence/SPEC-MOC.md"

set_test "no SPEC-MOC.md in dir -> SKIP (scan clean, no marker globbed)"
assert_exit_code 0 scan_root "$FIX/gate"

set_test "bare integer 1 WITH inline # comment -> GATED (guards inline-comment false-skip)"
assert_exit_code 0 moc_is_gated "$FIX/gate/gate-version-commented/SPEC-MOC.md"

section "MOC orphan lint — spec_id join (T014, FR-019)"

set_test "spec_id namespace-matches dir (prsg,002) -> PASS"
assert_exit_code 0 moc_specid_matches_dir "$FIX/specid/prsg-002-something/SPEC-MOC.md" "prsg-002-something"

set_test "spec_id namespace-matches dir (spec,006a) -> PASS"
assert_exit_code 0 moc_specid_matches_dir "$FIX/specid/006a-uat-skeleton/SPEC-MOC.md" "006a-uat-skeleton"

set_test "spec_id (spec,002) vs dir (prsg,002) collision -> VIOLATION"
assert_exit_code 1 moc_specid_matches_dir "$FIX/specid/prsg-002-collision/SPEC-MOC.md" "prsg-002-collision"

set_test "spec_id 013a1 vs dir 013a near-miss -> VIOLATION"
assert_exit_code 1 moc_specid_matches_dir "$FIX/specid/013a/SPEC-MOC.md" "013a"

set_test "absent spec_id in gated marker -> VIOLATION"
assert_exit_code 1 moc_specid_matches_dir "$FIX/specid/specid-absent/SPEC-MOC.md" "specid-absent"

set_test "empty spec_id in gated marker -> VIOLATION"
assert_exit_code 1 moc_specid_matches_dir "$FIX/specid/specid-empty/SPEC-MOC.md" "specid-empty"

section "MOC orphan lint — dogfood scan of the real spec trees"

# PRSG-002's own marker MUST be gated (guards the inline-comment false-skip on
# the real marker) and MUST pass both rules. Legacy specs carry no marker -> skipped.
PRSG_MARKER="$REPO_ROOT/specs/prsg-002-moc-templates/SPEC-MOC.md"
set_test "PRSG-002 marker is version-gated (observable, not inferred from exit 0)"
if moc_is_gated "$PRSG_MARKER"; then _pass; else _fail "PRSG-002 SPEC-MOC.md is NOT gated (inline-comment false-skip?)"; fi

set_test "real-tree scan of docs/ai/specs/ is clean (legacy skipped)"
assert_exit_code 0 scan_root "$REPO_ROOT/docs/ai/specs"

set_test "real-tree scan of specs/ is clean (PRSG-002 passes, legacy skipped)"
assert_exit_code 0 scan_root "$REPO_ROOT/specs"

# Compute final exit code from the self-test summary, then disarm the traps so
# a nonzero summary exit is NOT remapped to 2 by the ERR trap under set -e.
final_rc=0
test_summary || final_rc=$?
trap - ERR EXIT
exit "$final_rc"

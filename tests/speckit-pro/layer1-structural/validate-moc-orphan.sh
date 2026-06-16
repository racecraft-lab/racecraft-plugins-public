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
# The canonical MOC libs ship inside the plugin (FR-004); the test tree does not
# ship, so source them from their shipped home, not from this test tree's lib/.
MOC_LIB_DIR="$(cd "$(dirname "$0")/../../../speckit-pro/skills/speckit-autopilot/scripts/lib" && pwd)"
# shellcheck source=../lib/assertions.sh
source "$LIB_DIR/assertions.sh"
# shellcheck source=../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-id-normalize.sh
source "$MOC_LIB_DIR/moc-id-normalize.sh"
# shellcheck source=../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh
source "$MOC_LIB_DIR/moc-frontmatter.sh"

# errtrace: propagate the ERR trap into shell FUNCTIONS so an unexpected failure
# inside scan_root (e.g. a broken basename) trips the trap -> exit 2 (FR-020).
# Without -E the ERR trap is NOT inherited by functions and an internal failure
# would surface as set -e's raw exit code, not the contract's exit 2. Set AFTER
# the source lines (the libs' own `set -euo pipefail` does not clear -E).
set -E

# layer1-structural -> tests -> speckit-pro -> repo root.
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"

# Gate literal — KEEP IN SYNC with the scaffold template's stamped
# `structureVersion: 1` and moc-frontmatter.sh's gate. No shared version file.
# (The actual integer test lives in moc_is_gated; this comment marks the
# duplication intentionally per the lint-behavior contract.)
GATE_VERSION=1

# Global violation accumulator for the real-tree / arg scan path. scan_root
# RETURNS 0 and increments this; main decides exit 1 if > 0 else 0. This keeps
# the ERR trap LIVE when scan_root is called BARE (not in a `||` that suppresses
# set -e), so an unexpected internal failure -> exit 2 (FR-020), distinct from a
# content-violation exit 1 derived from the counter.
VIOLATION_COUNT=0

# ---------------------------------------------------------------------------
# Side-effect-free predicates (pure booleans; no printing, no exit). Safe to
# call inside assert_exit_code and under set -e when guarded by the caller.
# ---------------------------------------------------------------------------

# moc_up_well_formed <marker-file>
# Exit 0 iff `up:` is present, non-empty, and a well-formed relative `[]()`
# link. A `[[wikilink]]` form is NOT well-formed -> exit 1. Exit 1 if absent
# or empty. Does NOT resolve the target.
moc_up_well_formed() {
  local file="$1" up target before
  # Missing up: is an expected content violation, not an internal error. On
  # Bash 3.2 with errtrace, a failing command substitution assignment can still
  # fire ERR, so normalize the expected miss to an empty value explicitly.
  up="$(moc_frontmatter_field "$file" up 2>/dev/null || true)"
  [ -n "$up" ] || return 1                                # empty  -> violation
  # Reject the wikilink form outright (ill-formed for orphan).
  case "$up" in
    *'[['*) return 1 ;;
  esac
  # Require a well-formed inline link: `[text](target)` somewhere in the value.
  case "$up" in
    *'['*']('*')'*) : ;;                  # has [text](target) shape
    *) return 1 ;;
  esac
  # The target MUST be RELATIVE (FR-009). Extract the target between the first
  # `](` and the next `)`, trim surrounding whitespace, then reject non-relative
  # forms: an absolute URL or any URI scheme (e.g. `https://`, `mailto:`), a
  # protocol-relative (`//host`), root-absolute (`/path`), or anchor-only
  # (`#frag`). Accept only a genuinely relative path.
  target="${up#*](}"                       # drop up to first `](`
  target="${target%%)*}"                   # keep up to first `)`
  # Trim leading/trailing whitespace (bash 3.2-safe) so e.g. `]( /abs)` is caught
  # by the root-absolute arm below rather than slipping past the anchored glob.
  target="${target#"${target%%[![:space:]]*}"}"
  target="${target%"${target##*[![:space:]]}"}"
  [ -n "$target" ] || return 1             # empty/whitespace-only target -> violation
  case "$target" in
    *'://'*) return 1 ;;                    # absolute URL (any scheme)
    //*)     return 1 ;;                    # protocol-relative
    /*)      return 1 ;;                    # root-absolute
    '#'*)    return 1 ;;                    # anchor-only
  esac
  # Reject any other URI scheme (a colon appearing before the first slash),
  # e.g. `mailto:`, `tel:` — a parent roadmap link is never schemed.
  case "$target" in
    */*) before="${target%%/*}" ;;
    *)   before="$target" ;;
  esac
  case "$before" in
    *:*) return 1 ;;
  esac
  return 0
}

# moc_specid_matches_dir <marker-file> <dir-name>
# Exit 0 iff `spec_id` is present, non-empty, and namespace-matches <dir-name>
# under the ID-normalization grammar. Absent/empty spec_id -> exit 1.
moc_specid_matches_dir() {
  local file="$1" dir_name="$2" spec_id
  # Missing spec_id is an expected content violation; avoid tripping the global
  # internal-error trap for this predicate miss.
  spec_id="$(moc_frontmatter_field "$file" spec_id 2>/dev/null || true)"
  [ -n "$spec_id" ] || return 1                                    # empty
  moc_id_match "$spec_id" "$dir_name"
}

# ---------------------------------------------------------------------------
# Scan: evaluate the gated content rules over a scan root. RETURNS 0 always
# (never exits, never returns nonzero) and increments the GLOBAL VIOLATION_COUNT
# per violation, printing "path + which rule failed" to stdout. Returning 0
# keeps the ERR trap live when the caller invokes scan_root BARE — any
# UNEXPECTED set -e failure inside then trips the trap -> exit 2 (FR-020),
# distinct from the content-violation exit 1 main derives from VIOLATION_COUNT.
# ---------------------------------------------------------------------------

# scan_root <root-dir>
# For each immediate child spec directory under <root-dir>, gate on its
# SPEC-MOC.md (exempt-before-content) and apply the orphan + spec_id rules to
# gated markers only. A missing or empty root is SKIPPED (not an error).
scan_root() {
  local root="$1" spec_dir marker dir_name
  [ -d "$root" ] || return 0   # missing root -> skip (FR-022)

  for spec_dir in "$root"/*/; do
    [ -d "$spec_dir" ] || continue           # empty root -> glob stays literal
    case "$spec_dir" in
      */.process/*) continue ;;              # .process/** exempt
    esac
    marker="${spec_dir}SPEC-MOC.md"

    # Unreadable marker (FR-021/FR-023): a SPEC-MOC.md that EXISTS but is not
    # readable (permission denied) is SKIPPED with a stderr WARNING — never a
    # content violation. Checked BEFORE the gate so it is not silently dropped.
    # (A truly ABSENT marker falls through to the gate check, which SKIPs it
    # silently — no warning.)
    if [ -e "$marker" ] && [ ! -r "$marker" ]; then
      printf 'WARNING: validate-moc-orphan.sh: skipping unreadable marker %s\n' "$marker" >&2
      continue
    fi

    # Exempt-before-content (FR-023): gate decision uses ONLY the marker's
    # version field; no body read happens before this.
    if ! moc_is_gated "$marker"; then
      continue                               # no/absent/malformed marker -> SKIP
    fi

    dir_name="$(basename "$spec_dir")"

    # Orphan rule (MOC files only — the marker is the only SPEC-MOC.md here).
    if ! moc_up_well_formed "$marker"; then
      printf 'VIOLATION [orphan]: %s — up: missing, empty, or ill-formed (not a well-formed relative [](...) link)\n' "$marker"
      VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
    fi

    # spec_id join rule.
    if ! moc_specid_matches_dir "$marker" "$dir_name"; then
      printf 'VIOLATION [spec_id]: %s — spec_id absent/empty or does not namespace-match directory "%s"\n' "$marker" "$dir_name"
      VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
    fi
  done

  return 0
}

# ---------------------------------------------------------------------------
# Internal-error trap (FR-020): any UNEXPECTED set -e failure maps to exit 2 on
# stderr — distinct from a content violation (exit 1 on stdout). Disarmed
# before the deliberate final exit so a clean/violation exit is never remapped.
# ---------------------------------------------------------------------------
# NOTE: under `set -E`, a failed command-substitution-in-assignment inside a
# function fires ERR once in the function frame and again as the failure unwinds
# to main — and the two invocations do NOT share variable state, so an in-shell
# re-entrancy guard cannot dedupe them. The internal-error path may therefore
# emit this stderr line twice; the EXIT CODE is always 2 and the message is
# always on STDERR (never conflated with the stdout exit-1 violations), which is
# what the 3-way exit contract (FR-020/FR-024) requires.
_on_err() {
  local ec=$?
  printf 'ERROR: validate-moc-orphan.sh: internal failure (exit %d)\n' "$ec" >&2
  trap - ERR EXIT
  exit 2
}
trap _on_err ERR

# ---------------------------------------------------------------------------
# Mode A: explicit scan-root arg -> scan only that root, exit with its result.
# (This is the path the Layer-4 exit-code driver exercises.)
#
# scan_root is called BARE (not inside `||` or a command substitution) so the
# ERR trap stays LIVE: an UNEXPECTED internal failure -> exit 2 (FR-020), while
# a content violation (VIOLATION_COUNT > 0) -> exit 1. The two failure classes
# are never conflated (FR-024). The earlier KNOWN GAP (scan_root on the left of
# `||` suppressing set -e, leaving the trap inert and surfacing internal
# failures as exit 1) is fixed by the counter-based scan_root above.
# ---------------------------------------------------------------------------
if [ "$#" -ge 1 ]; then
  VIOLATION_COUNT=0
  scan_root "$1"
  trap - ERR EXIT
  if [ "$VIOLATION_COUNT" -gt 0 ]; then
    exit 1
  fi
  exit 0
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

set_test "absolute-URL up: is a violation (not a relative target)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-absolute-url-up/SPEC-MOC.md"

set_test "root-absolute up: is a violation (not a relative target)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-root-absolute-up/SPEC-MOC.md"

set_test "protocol-relative up: is a violation (not a relative target)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-protocol-relative-up/SPEC-MOC.md"

set_test "anchor-only up: is a violation (not a relative target)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-anchor-only-up/SPEC-MOC.md"

set_test "root-absolute up: with a LEADING SPACE is still a violation (trimmed)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-leading-space-up/SPEC-MOC.md"

set_test "schemed up: (mailto:/tel:) is a violation (not a relative target)"
assert_exit_code 1 moc_up_well_formed "$FIX/orphan/orphan-scheme-up/SPEC-MOC.md"

set_test "non-MOC docs in a gated spec are not required to carry up: (scan clean)"
VIOLATION_COUNT=0
scan_root "$FIX/scan-clean" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "non-MOC docs must not be required to carry up:"

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
VIOLATION_COUNT=0
scan_root "$FIX/gate" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "gate fixtures: only the gated-commented marker is checked and it passes orphan+spec_id"

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

section "MOC orphan lint — fixture-backed dogfood and real-tree scan"

# A committed fixture replaces the old live PRSG-002 marker dependency after
# merged spec folders are archived out of active `specs/**`.
DOGFOOD_MARKER="$FIX/specid/prsg-002-something/SPEC-MOC.md"
set_test "Dogfood PRSG marker is version-gated (observable, not inferred from exit 0)"
if moc_is_gated "$DOGFOOD_MARKER"; then _pass; else _fail "fixture SPEC-MOC.md is NOT gated"; fi

set_test "Dogfood PRSG marker spec_id namespace-matches its directory"
assert_exit_code 0 moc_specid_matches_dir "$DOGFOOD_MARKER" "prsg-002-something"

set_test "real-tree scan of docs/ai/specs/ is clean (legacy skipped)"
VIOLATION_COUNT=0
scan_root "$REPO_ROOT/docs/ai/specs" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "docs/ai/specs scan should find zero orphan/spec_id violations"

set_test "real-tree scan of specs/ is clean (active markers pass, legacy skipped)"
VIOLATION_COUNT=0
scan_root "$REPO_ROOT/specs" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "specs/ scan should find zero orphan/spec_id violations"

# Compute final exit code from the self-test summary, then disarm the traps so
# a nonzero summary exit is NOT remapped to 2 by the ERR trap under set -e.
final_rc=0
test_summary || final_rc=$?
trap - ERR EXIT
exit "$final_rc"

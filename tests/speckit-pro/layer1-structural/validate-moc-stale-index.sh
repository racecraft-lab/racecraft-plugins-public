#!/usr/bin/env bash
# validate-moc-stale-index.sh — Version-gated stale-index lint for MOC markers.
#
# For each version-gated `SPEC-MOC.md` (structureVersion bare-integer >= 1):
#   - resolution rule (FR-011): collect EVERY relative `[]()` link target — the
#     frontmatter `up:` value PLUS any body `[]()` links — and assert each
#     resolves to an existing REGULAR READABLE file, resolved relative to the
#     MOC's OWN directory. A target that exists but is NOT a regular readable
#     file (a directory, or a broken symlink) does NOT resolve — a violation
#     distinct from an absent target.
#   - wikilink rule (FR-012): NO `[[wikilink]]` may appear anywhere in the MOC;
#     any wikilink is a violation in its own right.
#
# Only relative targets are checked: absolute URLs (`http://`, `https://`,
# `mailto:`), root-absolute paths (`/...`), and pure in-document anchors (`#...`)
# are NOT relative file references and are skipped.
#
# Exempt -> SKIP (never a violation): no marker, no/unreadable fence,
# no/malformed/<1 structureVersion. The gate decision is made BEFORE any body
# read (exempt-before-content, FR-023), so legacy specs can never red-fail.
# An UNREADABLE marker is skipped with a stderr warning (FR-021/FR-023).
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
# shellcheck source=../../../speckit-pro/skills/speckit-autopilot/scripts/lib/moc-frontmatter.sh
source "$MOC_LIB_DIR/moc-frontmatter.sh"

# errtrace: propagate the ERR trap into shell FUNCTIONS so an unexpected failure
# inside scan_root (e.g. a broken dirname) trips the trap -> exit 2 (FR-020).
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

# Global violation accumulator for the real-tree / arg scan path. The scan
# function RETURNS 0 and increments this; main decides exit 1 if > 0 else 0. See
# the trap section below for WHY this is a counter (not a `||`-suppressed rc).
VIOLATION_COUNT=0

# ---------------------------------------------------------------------------
# Side-effect-free predicates (pure booleans; no printing, no exit). Safe to
# call inside assert_exit_code and under set -e when guarded by the caller.
# ---------------------------------------------------------------------------

# _stale_body <marker-file>
# Print the body of the marker — every line AFTER the closing `---` of the
# leading frontmatter fence. If the file has no leading `---` fence, the whole
# file is the body. TOTAL — never errors. Keeps the `up:` (frontmatter) value
# from being double-counted by the body link scan.
_stale_body() {
  local file="$1"
  [ -r "$file" ] || return 0
  awk '
    NR == 1 && $0 == "---" { infm = 1; next }
    infm && $0 == "---" { infm = 0; body = 1; next }
    infm { next }
    { print }
  ' "$file" 2>/dev/null || true
}

# _stale_link_targets <marker-file>
# Print, one per line, every RELATIVE `[]()` link target found in the marker:
# the frontmatter `up:` value (the (target) extracted from its markdown link)
# PLUS every body `[]()` link target. The body is read AFTER the frontmatter
# fence so the `up:` value is not double-counted. Absolute URLs, root-absolute
# paths, and pure `#anchor` references are filtered downstream. TOTAL.
_stale_link_targets() {
  local file="$1" up
  [ -r "$file" ] || return 0
  # up: value — extract the (target) from its `[text](target)` form, if present.
  up="$(moc_frontmatter_field "$file" up)" || up=""
  if [ -n "$up" ]; then
    printf '%s\n' "$up" \
      | grep -oE '\[[^][]*\]\([^()]*\)' 2>/dev/null \
      | sed -E 's/^\[[^][]*\]\(([^()]*)\)$/\1/' 2>/dev/null || true
  fi
  # Body `[]()` links only (frontmatter stripped above).
  _stale_body "$file" \
    | grep -oE '\[[^][]*\]\([^()]*\)' 2>/dev/null \
    | sed -E 's/^\[[^][]*\]\(([^()]*)\)$/\1/' 2>/dev/null || true
}

# _stale_is_relative_ref <target>
# Exit 0 iff <target> is a RELATIVE file reference worth resolving (not an
# absolute URL, not a root-absolute path, not a pure `#anchor`, not empty).
_stale_is_relative_ref() {
  local target="$1"
  [ -n "$target" ] || return 1
  case "$target" in
    \#*) return 1 ;;                         # pure in-document anchor
    /*) return 1 ;;                          # root-absolute path
    [a-zA-Z]*://*) return 1 ;;               # scheme:// URL (http, https, ...)
    mailto:*) return 1 ;;                    # mailto: link
  esac
  return 0
}

# _stale_target_resolves <marker-dir> <target>
# Exit 0 iff <target>, resolved relative to <marker-dir>, is an existing REGULAR
# READABLE file. A directory or a broken symlink at the path -> exit 1 (does NOT
# resolve). Strips any `#anchor` / `?query` suffix before resolving.
_stale_target_resolves() {
  local dir="$1" target="$2" path
  target="${target%%#*}"                     # drop #anchor
  target="${target%%\?*}"                    # drop ?query
  [ -n "$target" ] || return 1
  path="$dir/$target"
  # -f follows symlinks: a broken symlink fails -f (target absent) and a
  # directory fails -f (not a regular file) — both -> NOT resolved. -r requires
  # readability. This is exactly the "regular readable file" rule (FR-011).
  [ -f "$path" ] && [ -r "$path" ]
}

# moc_links_resolve <marker-file>
# Exit 0 iff the marker carries NO `[[wikilink]]` AND every relative `[]()`
# target (up: value + body links) resolves to a regular readable file relative
# to the marker's own directory. Exit 1 on the first wikilink or unresolved
# relative target. Side-effect-free (no printing). TOTAL/safe under set -e.
moc_links_resolve() {
  local file="$1" dir target
  [ -r "$file" ] || return 1
  dir="$(dirname "$file")"
  # Wikilink anywhere -> violation.
  if grep -q '\[\[' "$file" 2>/dev/null; then
    return 1
  fi
  # Every relative `[]()` target must resolve.
  while IFS= read -r target; do
    [ -n "$target" ] || continue
    _stale_is_relative_ref "$target" || continue
    if ! _stale_target_resolves "$dir" "$target"; then
      return 1
    fi
  done <<EOF
$(_stale_link_targets "$file")
EOF
  return 0
}

# ---------------------------------------------------------------------------
# Scan: evaluate the gated content rules over a scan root. RETURNS 0 always
# (never exits, never returns nonzero) and increments the GLOBAL
# VIOLATION_COUNT per violation, printing "path + which rule failed" to stdout.
# Returning 0 keeps the ERR trap live when the caller invokes scan_root BARE —
# any UNEXPECTED set -e failure inside then trips the trap -> exit 2, distinct
# from the content-violation exit 1 that main derives from VIOLATION_COUNT.
# ---------------------------------------------------------------------------

# scan_root <root-dir>
# For each immediate child spec directory under <root-dir>, gate on its
# SPEC-MOC.md (exempt-before-content) and apply the stale-index rules to gated
# markers only. A missing or empty root is SKIPPED (not an error). An unreadable
# gated marker is SKIPPED with a stderr warning (FR-021/FR-023).
scan_root() {
  local root="$1" spec_dir marker dir
  [ -d "$root" ] || return 0   # missing root -> skip (FR-022)

  for spec_dir in "$root"/*/; do
    [ -d "$spec_dir" ] || continue           # empty root -> glob stays literal
    case "$spec_dir" in
      */.process/*) continue ;;              # .process/** exempt
    esac
    marker="${spec_dir}SPEC-MOC.md"

    # Unreadable marker (FR-021/FR-023): a SPEC-MOC.md that EXISTS but is not
    # readable (permission denied) is SKIPPED with a stderr WARNING — never a
    # content violation. Checked BEFORE the gate so it is not silently dropped
    # as a generic "not gated". (A truly ABSENT marker falls through to the gate
    # check below, which SKIPs it silently — no warning.)
    if [ -e "$marker" ] && [ ! -r "$marker" ]; then
      printf 'WARNING: validate-moc-stale-index.sh: skipping unreadable marker %s\n' "$marker" >&2
      continue
    fi

    # Exempt-before-content (FR-023): gate decision uses ONLY the marker's
    # version field; no body read happens before this.
    if ! moc_is_gated "$marker"; then
      continue                               # no/absent/malformed marker -> SKIP
    fi

    dir="$(dirname "$marker")"

    # Wikilink rule first (its message is distinct from a dangling link).
    if grep -q '\[\[' "$marker" 2>/dev/null; then
      printf 'VIOLATION [stale-index/wikilink]: %s — contains a [[wikilink]] (wikilinks are not allowed in a gated MOC)\n' "$marker"
      VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
    fi

    # Resolution rule: name each specific relative target that fails to resolve.
    local target
    while IFS= read -r target; do
      [ -n "$target" ] || continue
      _stale_is_relative_ref "$target" || continue
      if ! _stale_target_resolves "$dir" "$target"; then
        printf 'VIOLATION [stale-index/link]: %s — relative link target does not resolve to a regular readable file: %s\n' "$marker" "$target"
        VIOLATION_COUNT=$((VIOLATION_COUNT + 1))
      fi
    done <<EOF
$(_stale_link_targets "$marker")
EOF
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
  printf 'ERROR: validate-moc-stale-index.sh: internal failure (exit %d)\n' "$ec" >&2
  # Clear ONLY the ERR trap (not EXIT): re-entrancy is prevented while the
  # deliberate `exit 2` still fires the EXIT trap, so Mode B's _cleanup_symlink
  # runs and the runtime broken-symlink fixture never leaks into the working tree
  # on the internal-error path. `exit 2` sets the status the EXIT trap preserves,
  # keeping the 3-way contract intact (FR-020). Mode A installs no EXIT trap, so
  # this is identical to the prior behavior there.
  trap - ERR
  exit 2
}
trap _on_err ERR

# ---------------------------------------------------------------------------
# Mode A: explicit scan-root arg -> scan only that root, exit with its result.
# scan_root is called BARE (not inside `||` or a command substitution) so the
# ERR trap stays live: an internal failure -> exit 2, while a content violation
# (VIOLATION_COUNT > 0) -> exit 1. This is the live-trap path the Layer-4
# exit-code driver exercises.
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

# The broken-symlink fixture target is created at runtime (a committed broken
# symlink is git/CI-fragile). Cleaned up on EXIT.
BROKEN_LINK="$FIX/stale/stale-broken-symlink/broken-link.md"
ln -sf "this-target-does-not-exist.md" "$BROKEN_LINK"
_cleanup_symlink() { rm -f "$BROKEN_LINK"; }
trap '_cleanup_symlink' EXIT

section "MOC stale-index lint — link resolution predicate (T012, FR-011)"

set_test "all relative targets resolve (up: + body link) -> PASS"
assert_exit_code 0 moc_links_resolve "$FIX/stale/stale-valid/SPEC-MOC.md"

set_test "an absent relative body-link target -> VIOLATION"
assert_exit_code 1 moc_links_resolve "$FIX/stale/stale-absent-link/SPEC-MOC.md"

set_test "a relative target that is a DIRECTORY (not a regular file) -> VIOLATION"
assert_exit_code 1 moc_links_resolve "$FIX/stale/stale-dir-target/SPEC-MOC.md"

set_test "a relative target that is a BROKEN SYMLINK -> VIOLATION (distinct from absent)"
assert_exit_code 1 moc_links_resolve "$FIX/stale/stale-broken-symlink/SPEC-MOC.md"

section "MOC stale-index lint — wikilink rule (T012, FR-012)"

set_test "a [[wikilink]] anywhere in a gated MOC -> VIOLATION"
assert_exit_code 1 moc_links_resolve "$FIX/stale/stale-wikilink/SPEC-MOC.md"

section "MOC stale-index lint — exempt-before-content (FR-013/FR-023)"

# A NON-gated marker (no structureVersion) whose links DANGLE must be skipped
# BEFORE any body read, so it never produces a stale-index violation. This is
# the load-bearing safety property behind SC-002 (legacy specs grandfathered).
# The `stale-not-gated` fixture carries a dangling body link but no version gate.
set_test "a non-gated marker with a dangling link is skipped (exempt-before-content)"
VIOLATION_COUNT=0
scan_root "$FIX/stale-exempt" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "not gated -> exempt-before-content -> no resolution attempted"

section "MOC stale-index lint — counter-based scan over the stale fixtures"

# Whole-tree scan of the stale fixtures: the 4 negative fixtures contribute
# violations; stale-valid contributes none. Observable through VIOLATION_COUNT
# (the scan returns 0 so the bare call keeps the trap live).
set_test "scan of the stale fixture tree counts the negative cases as violations"
VIOLATION_COUNT=0
scan_root "$FIX/stale" >/dev/null
# absent(1) + dir(1) + broken-symlink(1) + wikilink(1) = 4
assert_eq "4" "$VIOLATION_COUNT" "expected exactly the 4 negative stale fixtures to violate"

section "MOC stale-index lint — dogfood scan of the real spec trees"

# PRSG-002's own marker MUST be gated and its links MUST all resolve. Legacy
# specs carry no marker -> skipped.
PRSG_MARKER="$REPO_ROOT/specs/prsg-002-moc-templates/SPEC-MOC.md"
set_test "PRSG-002 marker is version-gated (observable, not inferred)"
if moc_is_gated "$PRSG_MARKER"; then _pass; else _fail "PRSG-002 SPEC-MOC.md is NOT gated"; fi

set_test "PRSG-002 marker links all resolve (up: -> roadmap)"
assert_exit_code 0 moc_links_resolve "$PRSG_MARKER"

set_test "real-tree scan of docs/ai/specs/ is clean (legacy skipped)"
VIOLATION_COUNT=0
scan_root "$REPO_ROOT/docs/ai/specs" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "docs/ai/specs scan should find zero violations"

set_test "real-tree scan of specs/ is clean (PRSG-002 passes, legacy skipped)"
VIOLATION_COUNT=0
scan_root "$REPO_ROOT/specs" >/dev/null
assert_eq "0" "$VIOLATION_COUNT" "specs/ scan should find zero violations"

# Compute final exit code from the self-test summary, then disarm the traps so
# a nonzero summary exit is NOT remapped to 2 by the ERR trap under set -e.
# Re-arm only the symlink cleanup on EXIT.
final_rc=0
test_summary || final_rc=$?
trap - ERR
_cleanup_symlink
trap - EXIT
exit "$final_rc"

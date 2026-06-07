#!/usr/bin/env bash
# validate-spec-index-determinism.sh — Layer 1 determinism fixture for the
# spec-index generator (sibling of validate-moc-orphan.sh).
#
# Runs generate-spec-index.sh (write mode) twice over a disposable copy of the
# committed fixture spec trees and asserts:
#   - the SECOND run is byte-identical to the first (zero diff)  [FR-003, SC-001]
#   - the generated output is independent of filesystem enumeration order: the
#     BACKLINKS rows appear in the fixed canonical precedence + LC_ALL=C path
#     order, the same on any machine                            [FR-005, SC-009]
#   - an out-of-scope legacy spec is left byte-for-byte unmodified [FR-007, SC-007]
#
# This is the SIMPLE assertions.sh shape (like test-moc-id-normalize.sh): source
# assertions.sh, resolve the generator into GEN, run, assert, test_summary. It
# does NOT reproduce validate-moc-orphan.sh's ERR-trap/exit-2 lint scaffolding —
# that 3-way-exit machinery is the generator's job, exercised as behavior here.
#
# Write mode MUTATES SPEC-MOC.md files, so the run operates on a mktemp copy; the
# committed fixtures under fixtures/spec-index/ are never touched.
#
# TDD RED: the generator does not exist yet. The FIRST assertion is a clean guard
# (generator present + executable) that fails with an interpretable message; the
# determinism/ordering assertions are paired with a "the first run actually
# changed something" gate so they cannot pass vacuously while the generator is
# absent. Output is a tidy "N/M passed (K failed)" summary + a non-zero exit,
# never a raw bash "No such file or directory" crash.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=../lib/assertions.sh
source "$HERE/../lib/assertions.sh"

# The single shared generator under test (sibling of reviewability-gate.sh). It
# lives in the shipped plugin tree; this test tree is a repo-root sibling of the
# plugin, so reach up to the repo root (../../../) and back into speckit-pro/.
GEN="$HERE/../../../speckit-pro/skills/speckit-autopilot/scripts/generate-spec-index.sh"

# Committed fixture spec trees (inputs only). The generator discovers spec dirs
# under `<REPO_ROOT>/specs/*/` (T009, data-model Discovery), so each fixture root
# carries a real `specs/<branch>/` layer. The determinism root holds ONLY
# renderable specs + one legacy skip — NO poison map — so a whole-root run is a
# clean exit 0 and a re-run is a zero-byte diff.
FIX="$HERE/fixtures/spec-index"
DET_SRC="$FIX/determinism"

# Disposable copy: write mode mutates the maps, so never run on the committed
# fixtures. trap-clean on EXIT; do NOT disarm the trap.
TMP="$(mktemp -d "${TMPDIR:-/tmp}/spec-index-l1.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
cp -R "$DET_SRC" "$TMP/root"
# TREE is the disposable REPO_ROOT handed to the generator; it contains specs/.
TREE="$TMP/root"

# Nested paths to the two maps the assertions read (under specs/<branch>/).
STALE_MOC="$TREE/specs/b-prsg-911-stale/SPEC-MOC.md"
LEGACY_MOC_SRC="$DET_SRC/specs/c-prsg-912-legacy/SPEC-MOC.md"
LEGACY_MOC_RUN="$TREE/specs/c-prsg-912-legacy/SPEC-MOC.md"

# snapshot <dir> — stable, order-independent content hash of every file under
# <dir>, used to compare whole-tree states between runs.
snapshot() {
  (cd "$1" && find . -type f -exec shasum {} + | LC_ALL=C sort)
}

# ───────────────────────────────────────────────────────────────────────────
section "RED guard — the generator must exist and be executable"
# ───────────────────────────────────────────────────────────────────────────
set_test "generator script exists at the contracted path"
assert_file_exists "$GEN" "FAIL: generator not found at $GEN"

set_test "generator script is executable"
assert_file_executable "$GEN" "FAIL: generator not executable at $GEN"

# ───────────────────────────────────────────────────────────────────────────
section "Determinism — a second write run yields a zero-byte diff (SC-001)"
# ───────────────────────────────────────────────────────────────────────────
# Capture the pristine state, then run the generator twice. NEVER invoke GEN bare
# under set -e (an absent file would abort the script) — capture rc with || true.
snap_pristine="$(snapshot "$TREE")"

rc1=0; "$GEN" "$TREE" >/dev/null 2>&1 || rc1=$?
set_test "first write run completes cleanly (exit 0)"
assert_eq "0" "$rc1" "first generator run must succeed over the in-scope fixtures"
snap_run1="$(snapshot "$TREE")"

rc2=0; "$GEN" "$TREE" >/dev/null 2>&1 || rc2=$?
set_test "second write run completes cleanly (exit 0)"
assert_eq "0" "$rc2" "second generator run must succeed"
snap_run2="$(snapshot "$TREE")"

# Honest-RED gate: the FIRST run must have CHANGED the tree (filled BACKLINKS/PRS,
# injected zones). If pristine == run1, the generator did nothing — a no-op
# generator must NOT be able to pass the idempotency check below vacuously.
set_test "the first run actually mutated the fixtures (not a no-op)"
if [ "$snap_pristine" != "$snap_run1" ]; then _pass; else _fail "first run changed nothing — generator is absent or inert"; fi

# The real idempotency gate: run1 == run2, byte-for-byte (zero diff on re-run).
set_test "second run is byte-identical to the first (zero diff, SC-001)"
assert_eq "$snap_run1" "$snap_run2" "re-run must yield a zero-byte diff (FR-003/SC-001)"

# ───────────────────────────────────────────────────────────────────────────
section "Order-independence — canonical BACKLINKS order, not readdir order (SC-009)"
# ───────────────────────────────────────────────────────────────────────────
# Output must depend only on the fixed precedence + LC_ALL=C path order, identical
# across machines regardless of filesystem enumeration order. The stale spec holds
# spec.md, plan.md, contracts/sample.md, .process/prs.json across four buckets.
moc_ord="$(cat "$STALE_MOC" 2>/dev/null || true)"
bz="${moc_ord#*GENERATED:BACKLINKS:START}"; bz="${bz%%GENERATED:BACKLINKS:END*}"

set_test "BACKLINKS contains the in-tree artifacts (renderer ran)"
assert_contains "$bz" "(spec.md)" "BACKLINKS must enumerate the spec's own artifacts (guards a vacuous order pass)"

set_test "spec.md precedes plan.md (fixed precedence, FS-order-independent)"
o_spec="${bz%%(spec.md)*}"; o_plan="${bz%%(plan.md)*}"
if [ "${#o_spec}" -lt "${#o_plan}" ]; then _pass; else _fail "spec.md must precede plan.md (FR-005/SC-009)"; fi

set_test "plan.md precedes contracts/ (fixed precedence, FS-order-independent)"
o_contract="${bz%%contracts/*}"
if [ "${#o_plan}" -lt "${#o_contract}" ]; then _pass; else _fail "plan.md must precede contracts/** (FR-005/SC-009)"; fi

set_test "contracts/ precedes .process/ (fixed precedence, FS-order-independent)"
o_proc="${bz%%.process/*}"
if [ "${#o_contract}" -lt "${#o_proc}" ]; then _pass; else _fail "contracts/** must precede .process/** (FR-005/SC-009)"; fi

# ───────────────────────────────────────────────────────────────────────────
section "Scope — an out-of-scope legacy spec is left byte-for-byte unmodified (SC-007)"
# ───────────────────────────────────────────────────────────────────────────
# The legacy spec is not version-marked, so both runs must leave it untouched.
legacy_pristine="$(shasum "$LEGACY_MOC_SRC" | awk '{print $1}')"
legacy_after="$(shasum "$LEGACY_MOC_RUN" | awk '{print $1}')"
set_test "the legacy (non-version-marked) map is unchanged after two runs"
assert_eq "$legacy_pristine" "$legacy_after" "FR-007/SC-007: legacy specs are skipped and left unmodified"

test_summary

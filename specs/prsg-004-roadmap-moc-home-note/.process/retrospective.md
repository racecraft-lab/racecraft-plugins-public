---
feature: prsg-004-roadmap-moc-home-note
branch: prsg-004-roadmap-moc-home-note
date: 2026-06-08
completion_rate: 95
spec_adherence: 100
requirements_total: 32
requirements_implemented: 32
critical_findings: 0
---

# Retrospective: Roadmap-MOC home note from PRD + coach the two-zone structure (PRSG-004)

## Executive Summary

PRSG-004 shipped its full scope: `speckit-prd` emits a third artifact (the roadmap-MOC
home note), `speckit-coach` teaches the two-zone model, and the dormant `render_index()`
in `generate-spec-index.sh` is activated context-scoped so only the home note's INDEX
fills repo-wide while every spec-MOC stays byte-identical. Spec adherence is **~100%**:
all 24 FRs and 8 SCs are implemented (none partial), verified against `spec.md`/`plan.md`
and the disk implementation. Full fast suite **1934/1934** (L1 439+428, L4 877, L5 190);
the new L4 generator group is **76/76** including the home-note INDEX-fill case (k) and
the FR-017a missing-INDEX fail-safe (l); the pinned PRSG-003 byte-identical contracts pass
unchanged. **0 CRITICAL / 0 SIGNIFICANT** findings.

## Requirement Coverage

- FR-001..FR-022 (incl. FR-015a, FR-017a, FR-020/021): **IMPLEMENTED**. Generator
  context-scoping (`is_home` threaded through `rebuild_map` 4th arg → `render_index` 2nd
  arg, default 0), home-note glob discovery disjoint from the `specs/` scan, FR-015a
  empty-`spec_id` skip, FR-017a exit-2 fail-safe, template carries the INDEX pair only,
  generator not duplicated into `codex-skills/`.
- SC-001..SC-008: **IMPLEMENTED**. Three-artifact emit, zero-new-question curated zone,
  >~10-epic advisory-not-block, determinism/idempotence (zero-byte second run),
  byte-identical spec-MOC path, relative `[]()` links, coach two-zone teaching, Codex
  parity (shared reference doc linked, not duplicated).

Spec Adherence % = (32 / 32) × 100 = **100%**.

## Notable Deviations

1. **L4 test-layer added (PLANNED / POSITIVE).** The roadmap catalog terse-listed PRSG-004
   as "Tests: L1" (skill-prompt-only assumption). Because US3 activates deterministic
   generator code, the spec adopted L1/L2/L3/L4/L8 — adding Layer 4 as the determinism
   fixture protecting SC-004/SC-005. Documented up front in spec.md "Test Coverage Note";
   adjudicated, not drift.

2. **Reviewability-gate BLOCK overridden twice (false positives).** The `reviewability-gate.sh`
   heuristics fired `block` at both tasks-phase and diff-phase. Tasks-gate: `reviewable_loc
   = task_count × 40` (24×40=960) and `total_files` deduped every path token (~98).
   Diff-gate: `total_files: 36` and `primary_surfaces: 5`. Both are counting artifacts —
   the authoritative plan-phase `estimate-reviewable-loc.sh` reported 7 production files /
   ~200 LOC / **pass**, and the real production diff is ~403 insertions across 7 files
   (well under the 800 block), the inflation coming from SDD spec/process docs, L4 fixtures,
   and eval JSON — none production review burden. Overrides were recorded with justification
   in the workflow log, consistent with the spec's single-spec split decision.

3. **One LOW code-review finding fixed (MINOR).** Home-note discovery used `find -type f`,
   which excluded a symlinked `*-roadmap-MOC.md` before the non-regular-file guard could
   run — leaving the guard dead and silently skipping a symlinked home note, inconsistent
   with the spec-MOC path. Fixed (commit ab16810) by dropping `-type f` so a symlinked home
   note fails safe with **exit 2**. Surfaced and resolved post-implementation; suite stayed
   green.

## Task Execution

23/24 tasks complete (95%). The single unchecked task is **T026** (generate the PR review
packet) — a bookkeeping gap, not spec drift: the PR body WAS generated and the PR opened
(workflow steps "PR Body Generation" / "PR Creation" complete). T026's checkbox simply was
not flipped.

## Constitution Compliance

All six articles **PASS** (re-verified at G7). No new plugin/manifest (I), `set -euo
pipefail` + ERR-trap→exit-2 discipline preserved (II), release-please owns versioning (III),
L4 determinism fixture + green suite (IV), `feat(speckit-pro):` commits (V), generator
extended in place — no new script, no lib extraction, advisory-not-block epic cap (VI).
**Violations: None.**

## Lessons Learned

1. **Path-sniffing avoidance paid off.** Threading an explicit `is_home` signal from the
   discovery site (rather than re-deriving target type by path inside `render_index`) kept
   the spec-MOC path provably byte-identical and the PRSG-003 contracts green — the highest-
   risk constraint, de-risked by design choice.

2. **TDD-first caught the dead guard early-ish but not the glob.** Writing the L4 fixture
   RED before activation proved the renderer, yet the `find -type f` symlink hole slipped
   past until code review — a reminder that a passing fixture only covers the cases the
   fixture enumerates; the spec-MOC symlink case existed but the home-note mirror of it did
   not until the review added it.

3. **Reviewability heuristics over-count SDD/test artifacts.** Both gate blocks were pure
   file-count/`task_count×40` artifacts inflated by spec docs, fixtures, and eval JSON. The
   plan-phase production-file estimator is the trustworthy signal; the count-based gate needs
   a production-vs-non-production filter to stop crying wolf on well-scoped specs.

4. **Catalog test-tier guesses need revisiting when scope touches code.** "Tests: L1" assumed
   prompt-only; activating generator code rightly forced L4. Catalog tiers are a planning
   hint, not a contract — re-deriving the test set from what the slice actually changes is
   the correct move.

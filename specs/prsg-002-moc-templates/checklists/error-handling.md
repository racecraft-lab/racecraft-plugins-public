# Error Handling Checklist: MOC templates + scaffold-time skeleton + version-gated lints

**Purpose**: Validate the QUALITY of the error-handling / exit-code / robustness requirements for the two version-gated lints — how an INTERNAL error is distinguished from a VIOLATION, how degenerate inputs (missing/garbled frontmatter, unreadable files, missing scan roots, no-args invocation) are handled, and the load-bearing guarantee that a grandfathered legacy spec can NEVER cause a nonzero exit. These are "unit tests for the requirements," not for the implementation.
**Created**: 2026-06-06
**Feature**: [spec.md](../spec.md)
**Focus**: Exit-code contract (violation vs internal-error vs clean), robustness of frontmatter parsing on degenerate/unreadable inputs, empty/missing scan roots, and the legacy-spec never-red-fail invariant.

## Exit-code contract — violation vs clean vs internal error

- [x] CHK001 - Is the exit-code contract specified well enough to distinguish an INTERNAL error (the lint itself cannot complete — e.g., an unreadable input, a missing scan root, an unparseable frontmatter block) from a content VIOLATION, given that under `set -euo pipefail` both surface as a nonzero exit? [Resolved — Spec §FR-020 three-way exit enum (0/1/2) + trap-to-2; §FR-024 distinct stderr reporting]
- [x] CHK002 - Is the violation → nonzero-exit (hard-fail) outcome specified for a version-gated spec? [Completeness, Spec §FR-014, lint-behavior-contract "Exit semantics"]
- [x] CHK003 - Is the no-violations → exit-success outcome specified for the set of checkable specs? [Completeness, Spec §FR-014, data-model "State / control flow"]
- [x] CHK004 - Is the exempt → SKIP (no violation, no nonzero contribution) outcome specified for a no-marker / no-`structureVersion` spec? [Completeness, Spec §FR-013, lint-behavior-contract "Exempt → SKIP"]
- [x] CHK005 - Is the exit-code semantics expressed as an enumerated decision (clean=success, violation-in-gated-spec=nonzero, internal/operational error=defined outcome) rather than only the two happy/violation rows, so an implementer knows which exit path an unexpected runtime failure takes? [Resolved — Spec §FR-020 enumerated 0/1/2 with trapped runtime failure → 2]

## Robustness of frontmatter parsing on degenerate inputs

- [x] CHK006 - Are requirements defined for a marker whose `structureVersion` is ABSENT (treated as not-gated → skip)? [Completeness, Spec §FR-013]
- [x] CHK007 - Are requirements defined for a marker whose `structureVersion` is MALFORMED / non-integer (quoted string, decimal, non-numeric → treated identically to absence → skip)? [Completeness, Spec §FR-013 malformed-value clause + Edge Cases "Marker present but structureVersion malformed"]
- [x] CHK008 - Are requirements defined for a `SPEC-MOC.md` that exists but has NO frontmatter block at all (no leading `---` fence), or a frontmatter block that is unparseable YAML — so the parser distinguishes "no readable `structureVersion`" (→ skip, safe) from "the marker is structurally broken"? [Resolved — Spec §FR-021: no fence / unparseable → no readable structureVersion → treated as absent → skip; + Edge Case "Marker with no/unparseable frontmatter"]
- [x] CHK009 - Is the parsing rule specified to be TOTAL on a structurally garbled marker — i.e., a frontmatter block that a YAML/`jq` parse would error on does not itself crash the lint and turn into an undistinguished nonzero exit? [Resolved — Spec §FR-021 "version-gate read MUST be total and MUST never crash the lint"; garbled → skip, not crash]
- [x] CHK010 - Are requirements defined for a degenerate `spec_id` / directory value in the normalization grammar (empty, all-alpha, leading/trailing dash) such that the derivation is total and never undefined? [Completeness, Spec §FR-017 totality clause + Edge Cases "Degenerate normalization inputs"]

## Unreadable / inaccessible inputs

- [x] CHK011 - Are requirements defined (or an explicit out-of-scope decision recorded) for a `SPEC-MOC.md` that exists but is UNREADABLE (permission-denied), so the lint's behavior is specified rather than an undefined `set -e` crash? [Resolved — Spec §FR-021: unreadable marker → exempt/skip + stderr warning, never a content violation; + Edge Case "Unreadable marker"]
- [x] CHK012 - Are requirements defined for an `up:` (or body link) whose target PATH exists but is not a regular readable file (e.g., a directory, a broken symlink), distinct from "target does not exist"? [Resolved — Spec §FR-011: non-regular-file target (dir / broken symlink) treated as not resolving → violation, distinct from absent; + Edge Case "Link target is a directory or broken symlink"]

## Scan-root / invocation robustness

- [x] CHK013 - Are requirements defined for the case where a configured scan root (`docs/ai/specs/` or `specs/`) does NOT exist or is empty — especially since the lints are required to be runnable in ANY consuming project (§FR-015), where one or both trees may be absent? [Resolved — Spec §FR-022: missing/empty scan root is skipped (not an error); scan whichever trees exist; + Edge Case]
- [x] CHK014 - Are requirements defined for a scan tree that contains ZERO version-gated specs (every spec is exempt) — the run must exit success, not error, on an effectively empty checkable set? [Resolved — Spec §FR-022: zero version-gated specs → exit 0 (success on empty checkable set)]
- [x] CHK015 - Is the repo-root / scan-root resolution mechanism specified deterministically (the `REPO_ROOT="$(cd ... && pwd)"` idiom), so the lints locate their scan trees the same way the existing Layer-1 validators do? [Completeness, plan.md "Repo-root resolution", lint-behavior-contract "Scan roots"]

## The legacy-spec never-red-fail invariant (load-bearing safety property)

- [x] CHK016 - Is the strong invariant stated — that a grandfathered legacy spec (no `SPEC-MOC.md`, or a marker without a valid integer `structureVersion`) can NEVER cause a nonzero exit REGARDLESS of its body content — by requiring that the exempt/skip decision is evaluated BEFORE any content read of that spec? [Resolved — Spec §FR-023 exempt-before-content invariant (skip decided before any body read); load-bearing behind SC-002]
- [x] CHK017 - Is the "first adoption produces zero new check failures on pre-existing legacy specs" outcome specified as a measurable success criterion? [Completeness, Spec §SC-002, §FR-013]
- [x] CHK018 - Is the dogfooded guarantee (the lints scan this repo's REAL legacy trees and stay green on day one because every legacy spec lacks the marker) stated and traceable to the actual directories present? [Traceability, Spec §FR-015, US2 AC-8, Assumptions "Repository dogfoods the contract"]

## Error message / observability quality

- [x] CHK019 - Are requirements defined for what a violation MUST report (which spec/file, which rule failed) so a nonzero exit is actionable rather than an opaque failure — distinguishing, in the output, a content violation from an operational failure? [Resolved — Spec §FR-024: violation reports offending file + failed rule; operational errors report to stderr distinctly (exit 2)]

## Acceptance criteria & measurability

- [x] CHK020 - Can the hard-fail-on-violation behavior be objectively verified via the stated acceptance scenarios (orphan-missing-`up:`, non-resolving link, wikilink) rather than a subjective "fails appropriately"? [Measurability, Spec §US2 AC-1, AC-2, AC-3]
- [x] CHK021 - Can the never-red-fail-on-legacy behavior be objectively verified (a no-marker spec is silently skipped and contributes no violation)? [Measurability, Spec §US2 AC-4, §SC-002]

## Notes

- Check items off as resolved: `[x]`.
- A "Resolved" tag marks an item that surfaced a missing/underspecified error-handling requirement and was closed by editing spec.md (and matching contract/data-model artifacts), not by changing implementation. The bracketed reference names the FR/section that now carries the rule.
- ALREADY-COVERED (do NOT re-flag): malformed/non-integer `structureVersion` → skip (FR-013); absent/empty `spec_id` → violation (FR-019); normalization grammar totality on degenerate inputs (FR-017). These pass as completeness checks above (CHK006/CHK007/CHK010).
- LOCKED (do NOT re-litigate): version-gate (no marker / no `structureVersion` = exempt/green); lints hard-fail (nonzero) on violation in a gated spec; lints MUST be green on this repo's legacy specs day one. These are phrased as consistency/completeness checks that the requirements ENCODE the settled decision.

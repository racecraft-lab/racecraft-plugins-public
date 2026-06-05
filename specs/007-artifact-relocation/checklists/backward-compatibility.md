# Backward-Compatibility Checklist: Artifact relocation — tiering, .process/, collapse

**Purpose**: Validate the quality, completeness, and consistency of the requirements that protect everything that already exists when this feature lands — specifically that the legacy specs (`specs/001..004,006a`) and the legacy `docs/ai/specs/SPEC-*-workflow.md` documents are neither moved, collapsed, nor mutated; that the new repo-root `.gitattributes` rule and the gate's new `.process/` arm degrade to no-ops over the existing change surface; that the pre-existing test suite (Layer-1/4/5) stays green alongside the feature's new checks; and that every Claude-skill prose edit stays in lockstep with its Codex mirror so the structural (L1) and parity (L8) layers do not break.
**Created**: 2026-06-05
**Feature**: [spec.md](../spec.md)

**Note**: These items are "unit tests for the requirements" — they test whether the spec/plan are written correctly for the backward-compatibility / no-regression angle, NOT whether the implementation works. This domain deliberately covers *what already exists and must not change*; the *forward* scoping-correctness angle is owned by `data-integrity.md` and the failure/idempotency angle by `error-handling.md` (cross-referenced where the three meet).

## Legacy Spec Directories Untouched (`specs/001..004,006a`)

- [ ] CHK001 - Is the new-specs-only boundary stated as a hard non-mutation guarantee — the feature MUST NOT migrate, move, or mutate any existing `specs/<NNN>/` directory — so the legacy spec directories (`specs/001..004,006a`) are provably untouched? [Completeness, Spec §FR-013, Out of Scope]
- [ ] CHK002 - Is it specified that no frontmatter stamp, file move, or in-place rewrite is applied to any legacy spec by THIS feature, with that retro-migration explicitly attributed to a separate later spec rather than left as an undefined boundary? [Clarity, Spec §FR-013, Out of Scope]
- [ ] CHK003 - Is the legacy-untouched guarantee consistent with the redirect requirements (FR-002/FR-003), so the `.process/` redirect is scoped to NEW scaffolding output and never reaches back into an existing `specs/<NNN>/` tree? [Consistency, Spec §FR-002/FR-003/FR-013]

## Legacy Same-Tree Documents Under `docs/ai/specs/` Stay Visible & Untouched

- [x] CHK004 - Does the spec state that the pre-existing `docs/ai/specs/SPEC-*-workflow.md` documents — which live in the SAME `docs/ai/specs/` tree that now receives new scaffold exhaust under `docs/ai/specs/.process/` — are NOT moved, collapsed, or mutated by this feature? [Completeness, Spec §FR-013] — RESOLVED: FR-013 now extends the non-mutation guarantee beyond `specs/<NNN>/` to the pre-existing `docs/ai/specs/SPEC-*-workflow.md` files (and the other pre-existing non-`.process/` files in that tree), stating they are not moved, relocated into `.process/`, frontmatter-stamped, or rewritten, and stay review-visible because the rules match the `/.process/` segment only.
- [ ] CHK005 - Is it specified WHY every pre-existing non-`.process/` file under `docs/ai/specs/` (the legacy workflow docs, the pipeline-verification runbook, the roadmap) stays review-visible — namely that the collapse glob and gate exclusion match the `/.process/` path segment ONLY, which a legacy doc path lacks — so the protection is traceable to the matching rule rather than assumed? [Clarity, Spec §Key Entities]
- [ ] CHK006 - Are the CONTRACT-set enumeration (Key Entities) and the new-specs-only boundary (FR-013) consistent in covering BOTH the `*-technical-roadmap.md` (named in Key Entities) AND the legacy `SPEC-*-workflow.md` documents that share the same tree, so no same-tree legacy file is left as an unaddressed collapse risk? [Consistency, Spec §Key Entities/FR-013]

## New Repo-Root `.gitattributes` Does Not Clobber Existing Config

- [ ] CHK007 - Does the spec/plan establish that the repository-root `.gitattributes` carrying the collapse rule is newly introduced for THIS repo (no pre-existing repo-root `.gitattributes` to merge with or overwrite), so the dogfood rule is an additive creation rather than a destructive rewrite? [Completeness, Plan §Source Code]
- [ ] CHK008 - Is the distinction between the dogfood repo's own `.gitattributes` (static, the lint target) and the consumer-side idempotent ensure-step consistent, so the two write paths are not conflated and neither retroactively rewrites the other repo's existing attributes? [Consistency, Spec §FR-007/FR-009, Plan §Phase 0]

## Gate Arm & Collapse Rule Degrade to No-Ops Over the Existing Surface

- [ ] CHK009 - Is it specified that the gate's new `.process/` exclusion arm leaves the reviewable-LOC count identical to its pre-feature value when a change contains zero `.process/` paths — so existing/legacy changes that touch no `.process/` path are accounted for exactly as before (the new arm degrades to a no-op)? [Completeness, Spec §FR-010, error-handling CHK009]
- [ ] CHK010 - Is the no-false-exclusion invariant stated — a changed path with no `/.process/` segment MUST NOT be excluded — so adding the arm cannot retroactively drop legacy non-`.process/` content out of the reviewable count? [Consistency, Spec §FR-010/FR-011, data-integrity CHK002]
- [ ] CHK011 - Is the collapse rule's effect bounded to `.process/` content only (it marks generated, never `-diff`, and matches the `/.process/` segment), so introducing the rule does not change how any pre-existing CONTRACT artifact is rendered or diffed? [Clarity, Spec §FR-008/FR-012]

## Pre-Existing Test Suite Stays Green (No Regression)

- [x] CHK012 - Does the spec/plan require that the pre-existing test suite (the already-wired Layer-1 structural, Layer-4 script-unit, and Layer-5 tool-scoping checks) continues to pass after the change, so the feature's success is gated on no-regression and not only on its NEW checks (SC-003/SC-005)? [Completeness, Spec §FR-015/SC-007] — RESOLVED: new FR-015 requires the pre-existing Layer-1/4/5 checks to keep passing (with the new lint added by extension and the Layer-4 tests additive), and new SC-007 makes it objectively verifiable — `bash speckit-pro/tests/run-all.sh` reports zero failures and a passing count at or above the pre-change baseline.
- [ ] CHK013 - Is the addition of the new Layer-1 lint specified to EXTEND the existing structural layer (registered into the run-all.sh L1 array) rather than replace or renumber existing validators, so existing L1 checks keep running unchanged alongside the new one? [Clarity, Plan §Source Code/Constitution Check IV]
- [ ] CHK014 - Is the extension of the two existing Layer-4 tests (`test-reviewability-gate.sh`, `test-ensure-reviewability-preset.sh`) specified as additive — new assertions appended, existing assertions preserved — so the pre-existing gate and ensure-step behavior remains covered and unbroken? [Consistency, Plan §Constitution Check IV]

## Codex Mirror Lockstep (L1 / L8 Do Not Break)

- [ ] CHK015 - Is the Codex-parity mandate stated as a hard requirement — every prose edit redirecting exhaust in a Claude skill MUST be mirrored identically into its Codex counterpart in the same change — so the structural parity validator and the parity fixtures are not broken by Claude-only drift? [Completeness, Spec §FR-006/AC-1.4/SC-006]
- [ ] CHK016 - Is "no Claude-only or Codex-only drift in the redirect targets" expressed as an objectively-verifiable outcome (identical `.process/` paths on both sides, zero drift), rather than a directional "should be similar" statement? [Measurability, Spec §SC-006]
- [ ] CHK017 - Is the parity guarantee traceable to the existing structural/parity coverage (the `validate-codex-skills.sh` L1 validator and the Layer-8 parity fixtures named in the plan), so "stays in lockstep" is anchored to stated, already-wired checks rather than assumed? [Traceability, Plan §Constitution Check IV/Testing]

## Out-of-Scope Boundaries Preserve Existing Behavior

- [ ] CHK018 - Is extension-authored exhaust (retrospective report, verify-tasks report) documented as explicitly OUT of scope and left at its existing review-visible location, so this feature does not retroactively change how those already-emitted artifacts appear? [Assumption, Spec §Out of Scope]
- [ ] CHK019 - Is the CONTRACT set documented as staying at its existing location (not moved), so reviewers and tooling that already reference `spec.md`/`plan.md`/`tasks.md` at their current paths see no breaking relocation? [Consistency, Spec §Out of Scope/Key Entities]

## Notes

- Items carrying a gap marker (the bracketed `Gap` dimension) indicate a missing or under-specified requirement that may need a spec/plan edit before implementation.
- The four locked scope decisions (linguist-generated only; new-specs-only; gate hardcodes the `.process/` glob; extension-authored exhaust out of scope) are treated as decided — items here test that the no-regression / backward-compatibility behavior under those decisions is clearly captured, NOT that scope should expand.
- This checklist's angle is *what already exists and must not change* (legacy specs, legacy same-tree docs, the pre-existing test suite, the existing CONTRACT locations, the Codex mirror). The forward scoping-correctness angle is owned by `data-integrity.md`; the failure/idempotency angle by `error-handling.md`.

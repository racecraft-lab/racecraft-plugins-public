# Specification Quality Checklist: Repository Bash Confinement and CI Dispatch Guard

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-08
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- This feature is intrinsically about developer tooling (a Bash-to-Python port,
  a CI confinement guard, and a release-notes composer), so some named surfaces
  (Python 3.11+, `.github/workflows/`, `bash`/`jq`) appear by necessity. They
  are treated as the subject matter of the requirements, not as prescribed
  implementation choices for an otherwise technology-agnostic feature; the
  active `speckit-pro-reviewability` preset expects this framing for
  harness/adapter specs.
- Success criteria are expressed as observable outcomes (zero `.sh` outside the
  workflow boundary, suite runs on Linux/macOS/Windows with only Python, 100%
  guard-block rate, readable Release Highlights) rather than internal metrics.
- All 11 design-concept decisions were accepted with recommended answers and
  the `estimate-spec-size` restoration was promoted into scope by operator
  directive, so no open clarifications remain.
- Items marked incomplete require spec updates before `/speckit-clarify` or
  `/speckit-plan`. No items are incomplete.

---

## Domain Checklist: Requirements Quality — Repository Bash Confinement and CI Dispatch Guard

**Generated**: 2026-07-08 by `/speckit-checklist requirements` (autopilot Phase 4)
**Domain focus** (from the workflow prompt): (1) every roadmap "Done When" bullet maps to ≥1 FR and ≥1 PR in the ~14-PR stack; (2) count-parity requirements stated per layer, not just globally; (3) release-notes requirements cover authoring, enforcement, composition, and skip paths; (4) the boundary between XPLAT-010 scope and XPLAT-008 UAT / XPLAT-009 completed work.
**Validates**: spec.md + plan.md together (post-Plan). This is a requirements-quality checklist ("unit tests for the requirements"), distinct from the Specify-phase spec-quality checklist above; both coexist per the `/speckit-checklist` append convention.

### A. Done When → FR + PR Traceability

- [ ] CHK001 Does every roadmap "Done When" bullet trace to at least one functional requirement AND at least one PR-stack slice? [Traceability, Spec §Requirements]
- [ ] CHK002 Is the zero-`.sh` scan requirement (excluding `.github/workflows/`, including extensionless Bash-shebang executables) defined and objectively measurable? [Completeness, Spec §FR-001, §SC-001]
- [x] CHK003 Is there a requirement that GitHub workflow shell snippets are limited to CI/CD dispatch glue with no embedded plugin validation, packaging, install, release, or runtime logic? [Resolved → Spec §FR-026] (Previously gap-marked: Done When bullet 2 mapped to no FR — FR-002 scopes the guard to files *outside* `.github/workflows/` and exempts workflow-internal shell. Remediated by adding FR-026, the affirmative complement that keeps workflow-internal shell reduced to dispatch glue calling Python gates; maps to the `pr-checks.yml` dispatch-swap PR, PR 5.)
- [ ] CHK004 Is there a requirement that active tests, evals, `.claude/hooks`, and helper tools run without Bash or `jq`? [Completeness, Spec §FR-009, §FR-014, §FR-015]
- [ ] CHK005 Are the already-Bash-free surfaces named in Done When bullet 3 (payload builders, release-readiness checks, install-verification paths, helper tools) bounded as prior/XPLAT-009-completed rather than in XPLAT-010's port scope? [Coverage, Spec §Assumptions]
- [ ] CHK006 Is the "CI fails on new Bash/active-invocation/`jq`" requirement defined and measurable (100% block rate)? [Completeness, Spec §FR-002, §FR-005, §SC-004]
- [ ] CHK007 Is the `estimate-spec-size` restoration expressed as a testable requirement with a defined result shape `{estimated_loc, suggested_slices, status}`? [Completeness, Spec §FR-025, §SC-007]

### B. Container / Runner Preflight (Done When bullets 4–5, 7)

- [ ] CHK008 Are the preflight-workflow trigger conditions (path-filtered PR + manual dispatch; never docs-only) specified? [Completeness, Spec §FR-017]
- [x] CHK009 Is there a requirement that the Linux container preflight exercises the *same* Python runner and release-gate entrypoints CI uses (not a divergent or reduced code path)? [Resolved → Spec §FR-027] (Previously gap-marked: Done When bullet 4 requires "using the same Python runner/release-gate entrypoints used by CI", but FR-017/018/020 and US4 stated only triggers, gating, and evidence — never the entrypoint-fidelity constraint. Remediated by adding FR-027; maps to the container-preflight PR, PR 11.)
- [ ] CHK010 Is the Linux-gating vs Windows-advisory (`continue-on-error`) distinction unambiguously specified? [Clarity, Spec §FR-018, §FR-019, §SC-008]
- [ ] CHK011 Is Windows runner-label unavailability / public-preview behavior specified as recorded-not-blocking? [Edge Case, Spec §FR-019, §Edge Cases]
- [ ] CHK012 Is the preflight evidence-upload requirement, and the "results MUST NOT be treated as native UAT" bound, defined? [Completeness, Spec §FR-020]

### C. Count-Parity Requirements (per layer, not just globally)

- [ ] CHK013 Are count-parity requirements stated at per-script granularity (finer than per-layer), rather than only as a global suite total? [Coverage, Spec §FR-011, §Key Entities: Count-Parity Baseline]
- [ ] CHK014 Is "runtime count" granularity defined so it captures loop-generated *and* non-loop grouped assertions (per assertion execution, not per former `set_test`)? [Clarity, Spec §FR-010]
- [ ] CHK015 Is a name-swap that preserves the same total explicitly required to be caught by name-level parity (not masked by an unchanged count)? [Coverage, Edge Case, Spec §FR-011, §SC-003]
- [ ] CHK016 Is the content each port PR's dual-run diff must carry enumerated (the six required items)? [Completeness, Spec §PR Review Packet Requirements, §Clarifications Session 1]
- [ ] CHK017 Is cumulative cross-stack parity evidence (running count ledger + final suite-parity result) required? [Completeness, Spec §FR-013]
- [ ] CHK018 Is the same-PR atomic swap (port + manifest flip + `.sh` delete) required so no layer ever runs with zero coverage? [Completeness, Spec §FR-012]
- [ ] CHK019 Is a per-layer manifest-vs-gate drift-guard (roster and dispatch kinds match the manifest) required, so per-layer composition cannot silently diverge? [Consistency, Spec §FR-007]

### D. Release-Notes Requirements (authoring / enforcement / composition / skip)

- [ ] CHK020 (authoring) Is the Release note block grammar specified (exactly one `release-note` fence, plain-English prose, an explicit allowed-inline-markdown subset)? [Clarity, Spec §FR-021]
- [ ] CHK021 (enforcement) Is the required `validate-release-note` check scoped to releasable conventional-commit types with defined trigger events (including `labeled`/`unlabeled`)? [Completeness, Spec §FR-022]
- [ ] CHK022 (skip) Is the `release-note/skip` exemption path defined for both the enforcement check and the composer's Highlights? [Coverage, Spec §FR-022, §FR-023]
- [ ] CHK023 (composition) Are the composer's Highlights composition, appendix preservation, and idempotency requirements specified? [Completeness, Spec §FR-023]
- [ ] CHK024 (composition) Is PR discovery specified precisely (Compare-API commit-subject walk, fail-loud on under-enumeration) rather than left ambiguous? [Clarity, Spec §FR-023]
- [ ] CHK025 (composition edge) Is composer behavior specified when zero PRs in range carry blocks, and when a harvested block is missing or malformed? [Edge Case, Spec §FR-023, §Edge Cases]
- [ ] CHK026 (composition edge) Is the first-release / no-previous-tag composer case dispositioned (explicitly in or out of scope)? [Coverage, research.md §D10]
- [ ] CHK027 (token/security) Is the composer's token scope (`contents: write` only; `RELEASE_PLEASE_TOKEN` forbidden; own job with non-inherited permissions) specified? [Completeness, Spec §FR-024]

### E. Scope Boundary: XPLAT-010 ↔ XPLAT-008 UAT / XPLAT-009 Completed

- [ ] CHK028 Is the XPLAT-009-completed work (plugin source + generated-payload Bash removal) explicitly excluded from XPLAT-010's port scope? [Coverage, Spec §Assumptions]
- [ ] CHK029 Is the requirement that XPLAT-008 native UAT remains the sole release-satisfying evidence — and that preflight never substitutes for it — stated? [Coverage, Spec §FR-020, §Assumptions]
- [ ] CHK030 Are the vendored `.specify/**` upstream helpers bounded as allowlisted-not-ported and `release_readiness_excluded`? [Consistency, Spec §FR-003, §FR-004]

### F. Cross-Cutting Requirement Quality

- [ ] CHK031 Is the PR-stack size described consistently across spec, plan, and design concept (the "13-PR" vs "14-PR" headline)? [Consistency, Spec §Reviewability Budget, plan.md §Summary] — Observation (non-blocking): spec §Reviewability Budget says "~13-PR stack", plan §Summary and the workflow file say "14-PR stack"; the divergence is a headline-count nuance (12 base numbered slices, with the 3a/3b and 7a/7b splits and the estimator counted differently), not a mapping error — the enumerated PR slices are identical across artifacts. Not a missing requirement; recorded for author awareness only.
- [ ] CHK032 Is the guard's detection vocabulary internally consistent (bash-scoped `.sh`/`.bash` + Bash-family shebang; `.ps1`/`.bat`/`.cmd`/`.zsh` out of scope; fixed 10-file allowlist)? [Consistency, Spec §FR-001, §FR-003, §SC-001]

### Domain Checklist Notes

- Coverage summary: 32 items across four prompt focus areas plus cross-cutting quality. 100% traceability satisfied (every item carries a `[Spec §…]`/`research.md §…` reference or a resolution tag).
- Focus areas selected: Done When→FR/PR traceability; per-layer count parity; release-notes authoring/enforcement/composition/skip; XPLAT-008/009 boundary. Depth: standard (formal post-Plan gate). Audience: reviewer (PR) + autopilot G4 gate.
- Gap remediation (this run): 2 gaps found and closed. CHK003 → added **FR-026** (workflow shell limited to dispatch glue; complements FR-002; maps to PR 5). CHK009 → added **FR-027** (preflight exercises the same runner/release-gate entrypoints CI uses; maps to PR 11). Both grounded in the roadmap's own Scope + "Done When" text. Post-remediation `count-markers` (gaps): spec 0 / plan 0 / checklists 0; G4 gate PASS. No items remain open for consensus.

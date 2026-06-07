---
feature: PRSG-002 — MOC templates + scaffold-time skeleton + version-gated lints
branch: prsg-002-moc-templates
date: 2026-06-06
completion_rate: 100%
spec_adherence: 100%
counts:
  requirements_total: 29   # 24 FR + 0 NFR + 5 SC
  fr: 24
  nfr: 0
  sc: 5
  tasks_total: 24
  tasks_completed: 24
findings:
  critical: 0
  significant: 0
  minor: 0
  positive: 2
constitution_violations: 0
generated_by: manual   # speckit.retrospective.analyze prerequisite script rejected the non-numeric branch
---

# Retrospective: PRSG-002 — MOC templates + scaffold-time skeleton + version-gated lints

## How this was generated

The `/speckit.retrospective.analyze` extension command exists at
`.claude/commands/speckit.retrospective.analyze.md`, but its step-1 context
initializer (`.specify/scripts/bash/check-prerequisites.sh --json
--require-tasks --include-tasks`) **aborts on this branch**:

```
ERROR: Not on a feature branch. Current branch: prsg-002-moc-templates
Feature branches should be named like: 001-feature-name, 1234-feature-name, ...
```

The branch-guard only accepts numeric / timestamp-prefixed branch names; the
PRSG- namespace prefix is non-numeric. This is a **non-fatal environmental
skip** — the command's analysis steps were executed manually against the
workflow log (`docs/ai/specs/.process/PRSG-002-workflow.md`), `spec.md`,
`plan.md`, `tasks.md`, and the commit history. No git mutations were made and
no Human-Gate spec-modifying handoff was triggered.

## Executive Summary

PRSG-002 shipped the MOC (Maps-of-Content) navigation layer for spec artifacts:
two template shapes, a scaffold-time minimal `SPEC-MOC.md` writer (Claude Code +
Codex), a shared namespace-aware ID normalizer, and two version-gated Layer-1
lints (orphan + stale-index). All 24 tasks completed; the full suite went
**1551 → 1640, all green** (G7 PASS), both lints are dogfood-green on this
repo's real (legacy + new) spec trees, and Codex parity held (74/74). Spec
adherence is effectively 100%: every FR and SC mapped to ≥1 completed task and
≥1 fixture/test.

The run was clean on outcomes but surfaced four process/code learnings worth
carrying forward (one design fork, one infra-resilience event, and two latent
parsing/discovery traps the implementation had to dodge), plus one positive
deviation (the checklist phase grew the spec by 5 FRs by catching real gaps).

## Proposed Spec Changes

**None.** No `spec.md` edits are recommended. The spec, plan, tasks, contracts,
and data-model are internally consistent and fully implemented. (Human Gate not
engaged — report-only.)

## Requirement Coverage Matrix

| Category | Count | Implemented | Partial | Not Implemented | Modified |
|----------|-------|-------------|---------|-----------------|----------|
| FR (FR-001..FR-024) | 24 | 24 | 0 | 0 | 0 |
| NFR | 0 | — | — | — | — |
| SC (SC-001..SC-005) | 5 | 5 | 0 | 0 | 0 |
| **Total** | **29** | **29** | **0** | **0** | **0** |

**Spec Adherence** = ((29 IMPLEMENTED + 0 MODIFIED + 0×0.5 PARTIAL) / (29 − 0 UNSPECIFIED)) × 100 = **100%**

FR→Task→fixture traceability is recorded in `tasks.md` and the workflow log's
Self-Review block. No orphan FRs and no orphan tasks.

## Success Criteria Assessment

| SC | Statement (abbrev.) | Status | Evidence |
|----|---------------------|--------|----------|
| SC-001 | scaffold-spec writes minimal `SPEC-MOC.md` (up/structureVersion/spec_id), Codex-mirrored | PASS | `specs/prsg-002-moc-templates/SPEC-MOC.md`; commit 5b8bfe5 + Codex mirror |
| SC-002 | Two MOC templates in plugin templates dir | PASS | `skills/speckit-coach/templates/{roadmap,spec}-moc-template.md` |
| SC-003 | Orphan + stale-index lints; `.process/**` exempt; no-marker skipped; wikilinks flagged | PASS | `tests/layer1-structural/validate-moc-{orphan,stale-index}.sh` + fixtures |
| SC-004 | Namespace-aware ID normalization (SPEC-002 ≠ PRSG-002; 013a ≠ 013a1) | PASS | `tests/lib/moc-id-normalize.sh`; `test-moc-id-normalize.sh` (22 assertions) |
| SC-005 | Version-gated, wired into run-all.sh, green on legacy specs day one | PASS | run-all.sh lines 145-146; 1640/1640; dogfood-green |

## Architecture Drift

| Planned (plan.md) | Implemented | Drift |
|-------------------|-------------|-------|
| Templates in plugin templates dir | `skills/speckit-coach/templates/` | None |
| Shared normalizer helper | `tests/lib/moc-id-normalize.sh` (+ version-gate helper) | None |
| Two Layer-1 lints | `validate-moc-{orphan,stale-index}.sh` | None |
| Layer-4 unit coverage "if warranted" | 2 Layer-4 drivers (normalizer + exit-code contract) | +1 file beyond plan (exit-code driver) — bounded, in-scope |
| scaffold-spec CC + Codex mirror | Both edited | None |

The single beyond-plan file (`test-moc-lint-exit-codes.sh`, a subprocess driver
for the 3-way 0/1/2 exit contract) is bounded test infrastructure, not scope
drift — it backs FR-020's exit-code enum that the checklist phase introduced.

## Significant Deviations

**None at CRITICAL or SIGNIFICANT severity.** All deviations from the original
Specify-phase scope were additive refinements ratified inside the workflow's own
gates (see Innovations). No dropped requirements, no scope creep into
PRSG-003/004/011 territory (verified at the Analyze gate).

## Innovations and Best Practices (Positive Deviations)

1. **Checklist phase earned its keep — spec grew 19 → 24 FRs.** The Specify
   phase landed 19 FRs; the data-integrity + error-handling checklists then
   closed 15 gaps and added FR-020..FR-024 (3-way exit enum + trap, total/safe
   marker parsing, scan-root robustness, exempt-before-content invariant,
   actionable output) plus the total/symmetric ID grammar. This is a positive
   deviation: the domain checklists caught correctness-critical error-handling
   gaps *before* implementation rather than in review. **Reusability:** strong
   signal to keep running data-integrity + error-handling checklists on any spec
   with a parsing/join correctness core. Constitution candidate: no (process
   already encoded in the autopilot workflow).

2. **Orchestrator recovered a dead sub-agent from primary evidence.** During the
   error-handling checklist remediation, the executor sub-agent died on an API
   socket error mid-task; the orchestrator completed the remediation from the
   primary evidence already on disk rather than restarting the phase. **Reusability:**
   validates the "recover-from-disk, don't restart" resilience pattern for
   long autopilot runs. Constitution candidate: no.

## Constitution Compliance

Constitution at `.specify/memory/constitution.md` (v1.1.0). All six principles
satisfied; **violations: None.**

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | Layer-1 structural green |
| II. Script Safety | PASS | `set -euo pipefail`; script-safety 55/55 |
| III. Semantic Versioning | PASS | No manual version edits (release-please owns it) |
| IV. Test Coverage Before Merge | PASS | New scripts have Layer-4 tests; 1640/1640 |
| V. Conventional Commits | PASS | All 15 branch commits well-formed `feat/docs/chore(...)` |
| VI. KISS / Simplicity / YAGNI | PASS | Shared single normalizer; ~350 LOC implementation surface |

## Unspecified Implementations

- **`update-agent-context.sh` injected a SPECKIT pointer block into top-level
  `CLAUDE.md`** (`<!-- SPECKIT START -->…plan.md…<!-- SPECKIT END -->`). Standard
  SpecKit behavior inside auto-managed markers, not authored by this spec. Flagged
  in the PR body for the maintainer to keep or drop at merge — **follow-up item**,
  not a violation.

## Task Execution Analysis

- 24/24 tasks `[X]` (100% completion). 5 TDD groups (A normalizer, B
  templates+scaffold, C1 orphan+gating+spec_id, C2 stale-index+exit-codes+wiring,
  D polish); 10 tasks `[P]`; RED-before-GREEN throughout; Codex-mirror edits
  paired with their CC edits (T007↔T008).
- Analyze gate: 3 findings, 0 CRITICAL → G6 PASS; pre-Implement confidence 0.94
  (≥0.90 → G6.5 PASS).

## Lessons Learned and Recommendations

1. **[HIGH] The locked design concept's spec_id↔directory join was wrong for
   this repo's sequential `specs/` numbering.** The design fork assumed a join
   model that collided with the flat sequential `specs/NNN-…` convention; it was
   resolved by maintainer choice at the Specify gate → **decision (A):
   namespace-prefixed directories**, with `spec_id` carrying the roadmap id (so
   `SPEC-002` and `PRSG-002` never collide).
   *Discovery point:* Specify. *Cause:* design-concept assumption vs. repo
   convention mismatch. *Prevention:* when scaffolding a spec whose id namespace
   differs from the repo's directory-numbering scheme, validate the join model
   against the actual `specs/` layout during grill-me, not at Specify.

2. **[HIGH] `run-all.sh` test discovery is hardcoded literal arrays, not globs —
   a new test is silently dropped until wired in.** The Layer-1 and Layer-4
   runners enumerate files by explicit path (run-all.sh lines 145-146 and
   232-233), so a freshly-added `validate-moc-*.sh` / `test-moc-*.sh` does not
   run — and produces no failure — until its path is manually appended.
   *Discovery point:* Implementation. *Cause:* discovery-by-array, not by glob.
   *Prevention:* treat "add the new script to the run-all.sh array" as a
   non-optional task step; longer-term, consider globbing the layer dirs so new
   tests are auto-discovered (a fail-open trap today).

3. **[HIGH] `structureVersion` inline-comment parsing trap would have falsely
   skipped the dogfood marker.** The template/marker line is
   `structureVersion: 1          # keep in sync with the lint scripts' hardcoded
   literal`. A naive "value = everything after the colon" parse captures
   `1          # keep in sync…`, which fails the integer `>= 1` gate, so the lint
   would treat a version-gated marker as ungated and **skip** the check it was
   meant to enforce. The lints correctly parse the bare leading integer (noted in
   their headers as "structureVersion bare-integer >= 1").
   *Discovery point:* Implementation. *Cause:* YAML scalar with a trailing
   `#`-comment. *Prevention:* any frontmatter value used as a gate/predicate must
   strip inline comments and surrounding whitespace before comparison; add a
   fixture with an inline-comment value (already covered under `fixtures/moc/gate/`).

4. **[MEDIUM] Long autopilot runs need disk-recoverable sub-agents.** A checklist
   executor died on an API socket error mid-remediation; the orchestrator
   recovered from primary evidence on disk rather than restarting. Worked here —
   keep designing phases so partial progress is durable and resumable, never
   restart-only.

5. **[MEDIUM] Domain checklists are high-leverage on correctness-critical specs.**
   The data-integrity + error-handling checklists grew the spec from 19 → 24 FRs
   by catching real error-handling/parsing gaps pre-implementation. Continue
   pairing these two domains on any spec with a parsing or join correctness core.

6. **[LOW] Branch-guard blocks the retrospective extension on non-numeric
   branches.** `check-prerequisites.sh` rejects the PRSG- prefix, forcing manual
   execution of this analysis. If PRSG-style namespaces become common, consider
   relaxing the branch-guard regex to accept an alpha-prefixed namespace, or
   documenting the manual-fallback path in the autopilot post-phase.

## File Traceability Appendix

| Surface | Path |
|---------|------|
| Spec | `specs/prsg-002-moc-templates/spec.md` |
| Plan | `specs/prsg-002-moc-templates/plan.md` |
| Tasks | `specs/prsg-002-moc-templates/tasks.md` |
| Workflow log | `docs/ai/specs/.process/PRSG-002-workflow.md` |
| MOC templates | `speckit-pro/skills/speckit-coach/templates/{roadmap,spec}-moc-template.md` |
| Scaffold marker | `specs/prsg-002-moc-templates/SPEC-MOC.md` |
| Shared normalizer | `speckit-pro/tests/lib/moc-id-normalize.sh` |
| Orphan lint | `speckit-pro/tests/layer1-structural/validate-moc-orphan.sh` |
| Stale-index lint | `speckit-pro/tests/layer1-structural/validate-moc-stale-index.sh` |
| Layer-4 drivers | `speckit-pro/tests/layer4-scripts/test-moc-{id-normalize,lint-exit-codes}.sh` |
| Suite wiring | `speckit-pro/tests/run-all.sh` (lines 145-146, 232-233) |
| PR | #116 — https://github.com/racecraft-lab/racecraft-plugins-public/pull/116 |

## Self-Assessment Checklist

- Evidence completeness: **PASS** — every deviation cites a file/task/commit/line.
- Coverage integrity: **PASS** — all 24 FR + 5 SC IDs accounted for; 0 NFR (none defined).
- Metrics sanity: **PASS** — completion 24/24=100%; adherence 29/29=100%.
- Severity consistency: **PASS** — labels match impact (0 CRITICAL/SIGNIFICANT; 2 POSITIVE).
- Constitution review: **PASS** — violations explicitly stated as None.
- Human Gate readiness: **PASS** — no spec changes proposed; gate not engaged.
- Actionability: **PASS** — 6 prioritized, evidence-tied recommendations.

---
feature: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract
branch: car-002-capability-probing-telemetry
date: 2026-07-17
mode: report-only (no spec.md/plan.md/tasks.md mutations)
completion_rate: 100
spec_adherence: 100
total_requirements: 36
functional_requirements: 28
success_criteria: 8
non_functional_requirements: 0
critical_findings: 0
significant_findings_resolved_in_run: 3
minor_findings: 2
positive_findings: 4
proposed_spec_changes: 2
proposed_spec_changes_applied: 0
constitution_violations: 0
pr: "#369 (open, mergeable)"
final_suite: 3199/3199 (offline, zero live model calls)
snapshot: CAR-002-RCS-2026-07-17-V3
---

# Retrospective: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

> Report-only analysis. Per the retrospective extension contract and the operator's
> instruction, this document ANALYZES the completed run and proposes changes; it does
> NOT modify `spec.md`, `plan.md`, or `tasks.md`. All proposed spec changes below are
> listed for consideration only and require explicit human approval before any edit.

## Executive Summary

CAR-002 completed all seven SpecKit phases and shipped as PR #369 (open, mergeable,
CI green). All 40 tasks are complete (100%), all 28 functional requirements and all 8
success criteria are implemented, and the constitution passed 6/6 at every gate. The
default suite is 3199/3199 offline with zero live model calls, adding +372 deterministic
tests over the Phase-0 baseline. Spec adherence is 100% — no dropped requirements, no
scope creep, no architectural drift from the plan.

The run's value is not in the (clean) final metrics but in three in-run correctness/
privacy defects that were caught and remediated before merge, and one process conflict
that was surfaced rather than silently resolved. None survives into the shipped artifact,
so there are zero open critical findings; but each produced a durable, reusable lesson:

1. A committed snapshot leaked run-local session UUIDs because the sanitizer only
   normalized home paths — caught by the tree-wide privacy scan, fixed by broadening
   sanitization and re-probing (V1 to V2).
2. An independent post-implementation code review caught a CAP-Q5 mis-derivation (the
   parser read the parent `-p` session's `modelUsage` as a subagent soft-remap when the
   subagent had actually hard-rejected) plus a dead-code fail-closed disposition
   (unparseable payloads did not abort the write). Both fixed with TDD, and the snapshot
   re-probed (V2 to V3) rather than hand-edited.
3. Three checklist-executor dispatches and one clarify-executor dispatch died on API
   stream timeouts, forcing a mid-run switch from the executor pattern to
   phase-executor generation with orchestrator-owned remediation.
4. The advisory atomicity classifier returned `one-navigable-PR`, conflicting with the
   operator-ratified 3-work-package `split-PR` decision. The conflict was recorded at
   G5 and deferred to the final reviewability gate with real diff numbers, not papered
   over.

## Proposed Spec Changes (proposals only — 0 applied)

These are candidate improvements surfaced by the retrospective. **None are applied.**
Each requires explicit human approval, and most are better targeted at a future
contract revision or a downstream CAR spec than at CAR-002's now-complete `spec.md`.

| # | Target | Proposal | Rationale | Priority |
|---|--------|----------|-----------|----------|
| PSC-1 | FR-024 (or a new FR) / CAR-003 consumer validation | Require deterministic validation to **re-derive** at least the CAP-Q5 outcome classification from each committed raw-evidence payload, not only structurally validate it. | The V2 mis-classification passed the full suite unchanged because the tests check schema-validity, sanitization, and hash reproduction — but never re-derive the outcome from the stored bytes. Since FR-012 commits the complete raw payload, outcome re-derivation is feasible and would have caught the defect in CI. | HIGH |
| PSC-2 | Schema contract (`claude-trace-contract.schema.json`) | Remove or explicitly document the unreachable enum value `not_applicable_subscription` (LOW-1 from code review), left in place as harmless. | Dead enum members invite future mis-use; a one-line comment or removal keeps the contract honest. This is schema tidiness, not a `spec.md` FR change. | LOW |

Human Gate note: per the extension's Section 13, if either proposal is accepted, the
spec-modifying action must be confirmed separately (`y`/`yes`). Default is NO; nothing
is edited by this report.

## Requirement Coverage Matrix

All 36 requirements (28 FR + 8 SC, 0 NFR) are IMPLEMENTED. No requirement is partial,
modified-as-drift, dropped, or unspecified. Coverage is enumerated by concern group so
no ID is missing.

| Concern group | Requirement IDs | Status | WP | Evidence |
|---|---|---|---|---|
| Probe execution boundary & determinism | FR-001, FR-002 | Implemented | WP1/WP3 | Single live `subprocess` boundary in `claude_capabilities.py` (T011); suite offline 3199/3199 (T037) |
| Probe matrix & budget | FR-003, FR-004, FR-005 | Implemented | WP1 | 37→6 tuple dedupe + budget/timeout/no-retries + fixed canary (T009/T010); join in T035 |
| Capability answers CAP-Q1..Q6 | FR-006, FR-007, FR-008 | Implemented | WP1 | Snapshot records CAP-Q1..Q6; CAP-Q6 open (detection-rule-only) (T012) |
| Unavailable-model probe CAP-Q5 | FR-009, FR-010 | Implemented | WP1 | Dual surface (`print_model` + `subagent_frontmatter`), both `hard_rejection` with FR-010 unset-proof (T012/T014) |
| Snapshot artifact & evidence | FR-011, FR-012, FR-013, FR-014 | Implemented | WP1 | Canonical snapshot V3, `<home>`+session-UUID sanitized, SHA-256 over sanitized bytes, subscription auth recorded (T015/T016/T017) |
| Schema contracts | FR-015, FR-016, FR-017 | Implemented | WP1 | One JSON Schema, four `$defs`, stdlib validator, platform-neutral (T003/T004/T005) |
| Telemetry capability profile | FR-018, FR-019, FR-020 | Implemented | WP2 | Versioned profile `CAR-002-TP-2026-07-17-V1`, 18 fields, exactly-one-label, nulls preserved (T019-T021/T023) |
| Trace contracts | FR-021, FR-022 | Implemented | WP2 | `route_resolution` bindings incl. `dispatch_namespace`/`parent_session_configuration`; telemetry-linkage rule (T022/T024) |
| Validation enforcement & record classes | FR-023, FR-024, FR-025 | Implemented | WP1/WP3 | Fail-closed writer wired; class-invariant + integrity + 37-route join checks; 4 record-class fixtures (T006/T033-T036) |
| Evidence authority | FR-026, FR-027 | Implemented | WP1 | Canonical-docs-only sourcing; labeled observation vs certified fact (T012/T020) |
| Repository integration | FR-028 | Implemented | WP1 | Validator registered in `suite-manifest.json`; Layer 4 coverage (T007) |
| Success criteria | SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008 | Implemented | all | See Success Criteria Assessment below |

**Spec Adherence** = ((36 implemented + 0 modified + 0*0.5) / (36 total − 0 unspecified)) × 100 = **100%**.

## Success Criteria Assessment

| SC | Statement (abbrev.) | Status | Evidence |
|----|---------------------|--------|----------|
| SC-001 | Snapshot addresses all six CAP-Q in one bounded run | Met | V3 snapshot records CAP-Q1..Q6 (CAP-Q6 explicitly open) |
| SC-002 | Zero live model calls in any repo/CI test; suite passes offline | Met | 3199/3199 offline, no `claude` CLI, no network (T037) |
| SC-003 | All four record classes have committed fixtures checked every run | Met | success/null/unavailable/misdelivery fixtures validated (T033) |
| SC-004 | No invalid observation reaches the snapshot (100% abort) | Met | Fail-closed writer wired into write path (MEDIUM-1 fix, `318087c5`) |
| SC-005 | All 37 routes resolve to exactly one tuple, derived not persisted | Met | 37→6 join, fails closed on zero/multi-resolve (T035) |
| SC-006 | Every telemetry field exactly-one label, nulls preserved | Met | 18-field profile validated against `telemetryProfile` `$def` (T023) |
| SC-007 | Reviewer can check all four contracts from one schema, no Python | Met | Single platform-neutral JSON Schema, four `$defs` (T003) |
| SC-008 | Downstream CAR spec binds records without any CAR-002 capability question | Met | CAR-003 handoff exercised by committed `route-resolution.json` (T026) |

## Architecture Drift

No architecture drift. Every file, module name, and structural decision matches the
plan's Declared File Operations and Structure Decision.

| Plan decision | Implemented as | Drift |
|---------------|----------------|-------|
| One JSON Schema, four `$defs`, draft 2020-12, under `docs/ai/research/` | `claude-trace-contract.schema.json` (294 lines) | None |
| Stdlib validator mirroring CAR-001 `validate_manifest` | `claude_trace_schema.py` (240 lines) | None |
| Operator-only probe tool, single live `subprocess` boundary | `claude_capabilities.py` (1421 lines) | None |
| Canonical snapshot, re-probe replaces in place, `V<n>` bumps | Snapshot at V3 (V1→V2→V3 chain in git history) | None |
| Route→tuple join derived, never persisted (constitution VI) | Recomputed each run from CAR-001 manifest | None |
| Snake_case importable modules vs kebab-case scripts | Both new modules snake_case as planned | None |
| 3 vertical work packages WP1→WP2→WP3 | Preserved as commit groups; PR-boundary resolved at final gate | See Significant Deviations #4 (process, not architecture) |

Note on size: the plan hand-estimated WP1 at ~550-820 reviewable LOC; the final diff
measured ~2,236 production reviewable LOC across the feature (over the 800 block
ceiling). This is a magnitude the mechanical estimator was structurally blind to (it
recognizes only `src/|app/|lib/|scripts/` or JS/TS/SQL, and every CAR-002 file is
test-tree `.py` or `docs/**` JSON). This is a known-and-documented estimator limitation,
not implementation drift — the design and file set are exactly as planned.

## Significant Deviations (all discovered and resolved in-run; 0 open)

### SD-1 — Session-UUID privacy leak in the committed snapshot (SIGNIFICANT, resolved)
- **Discovery point**: Implementation (tree-wide privacy scan after T015 operator run).
- **What happened**: The first operator probe committed a snapshot whose raw evidence
  still contained run-local session UUIDs; the sanitizer normalized home paths (FR-012)
  but not session identifiers.
- **Cause**: Spec gap — FR-012/FR-013 named "home/user paths" and "machine-local session
  paths" but the sanitizer implementation only covered `<home>` normalization.
- **Resolution**: Sanitization broadened to redact session UUIDs; re-probed to V2
  (commit `1185a3c1`). The V3 snapshot confirms `sanitization` marker
  `home_paths_and_session_ids_normalized_utf8`.
- **Prevention**: Add a sanitization-completeness unit assertion (the validator now
  re-scans committed payloads for unsanitized home/user/session paths — FR-024/T036,
  now continuously enforced).

### SD-2 — CAP-Q5 mis-derivation: parent-session model read as subagent soft-remap (SIGNIFICANT, resolved)
- **Discovery point**: Independent post-implementation code review (MEDIUM-2).
- **What happened**: The subagent-frontmatter surface parser read the parent `-p`
  session's `modelUsage` as evidence of a subagent soft-remap — a false availability
  signal on CAP-Q5 — when the subagent had actually hard-rejected the unavailable model.
- **Cause**: Misunderstanding of the surface semantics (`modelUsage` provenance) plus a
  test blind spot: structural validation of the committed snapshot never re-derived the
  outcome classification, so the wrong reading passed the suite unchanged.
- **Resolution**: Classification made surface-aware (parent model never populates the
  subagent's observed model), fixed with TDD RED→GREEN (commit `318087c5`), then
  **re-probed to V3** (commit `7f47386a`) so committed evidence is correct — both
  surfaces now `hard_rejection`, `remap_flagged: false`. Re-probing (not hand-editing
  evidence) is the honest fix.
- **Prevention**: See Proposed Spec Change PSC-1 (re-derive outcome from committed raw
  evidence in CI). A durable memory note records the "green suite ≠ committed-artifact-
  correct" gotcha.

### SD-3 — Fail-closed disposition was dead code (SIGNIFICANT, resolved)
- **Discovery point**: Independent post-implementation code review (MEDIUM-1).
- **What happened**: The "Partial probe matrix" fail-closed disposition for unparseable
  `--output-format json` payloads existed but was not wired into the write path, so an
  unparseable payload would not abort the write (nominally violating FR-023/SC-004).
- **Cause**: Process skip — the disposition logic was implemented but the writer never
  called the gate.
- **Resolution**: `gate_probe_run_dispositions` wired into the write path with TDD
  coverage (commit `318087c5`); the fail-closed writer now rejects both schema-invalid
  and unparseable payloads.
- **Prevention**: Teeth-test every declared error disposition against a triggering input,
  not only the happy path (now covered).

### SD-4 — Atomicity route vs. ratified 3-WP split conflict (PROCESS, surfaced not silently resolved)
- **Discovery point**: Tasks / G5 gate.
- **What happened**: The advisory atomicity classifier returned `one-navigable-PR`,
  disagreeing with the operator-ratified 3-WP `split-PR` decision (design concept Q8,
  Clarify consensus log #5).
- **Cause**: Scope evolution / tooling boundary — the classifier reads structural seams,
  not the operator's standing scope intent; split-emission machinery is deferred for
  installed workflows.
- **Resolution**: Both positions recorded at G5; the PR-boundary decision deferred to the
  final reviewability gate with real diff numbers. Final: a single navigable PR with a
  documented over-ceiling exception, WP1→WP2→WP3 review order preserved as commit groups
  for reviewer navigation. This is the exact contingency Q8 contemplated. Precedent:
  CAR-001 and G56R-001 shipped the same way.
- **Prevention**: This is the desired behavior — surface the conflict, defer to real
  numbers. Worth codifying as a reusable pattern (see below).

## Innovations & Best Practices

| # | What | Why it is better | Reusability | Constitution candidate? |
|---|------|------------------|-------------|-------------------------|
| POS-1 | **Re-probe over hand-edit** for corrected evidence (V2→V3) | Committed evidence stays a faithful capture, not a human patch; keeps the "evidence is recorded, never assumed" posture (FR-026) | Any capture-evidence spec | Candidate (evidence-integrity principle) |
| POS-2 | **Surface conflicts, defer to real numbers** (G5 atomicity vs ratified split) | Avoids both premature re-slicing and silently overriding operator intent; the true arbiter (diff-mode gate) decides last | Any reviewability/PR-boundary decision | Candidate |
| POS-3 | **Derive-by-join, never persist** the 37-route→tuple map | Eliminates a drift surface; the join key already lives in the CAR-001 manifest (constitution VI in action) | Any cross-artifact reference | Already codified (constitution VI) |
| POS-4 | **Executor-resilience fallback**: on API stream timeouts, drop from executor pattern to phase-executor + orchestrator remediation | Kept the run moving without losing determinism or record-grounding; zero consensus escalations | Any long autopilot run | Process note, not constitution |

## Constitution Compliance

**Violations: None.** All six principles PASS, verified at initial, post-design, and
final (post-Implement) checks.

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Plugin Structure Compliance | PASS | No plugin/manifest/agent/skill/hook added; all tooling under `tests/speckit-pro/`; Layer 1 green |
| II. Cross-Platform Runtime & Script Safety | PASS | Both modules Python 3.11 stdlib-only; `subprocess` argument-array `shell=False`; no new Bash/jq; single live boundary is operator-only |
| III. Semantic Versioning | PASS (n/a) | No `plugin.json` version change; schema `schema_version` const `1.0.0` is a contract identity, not a plugin semver |
| IV. Test Coverage Before Merge | PASS | +372 Layer-4 tests; validator registered in `suite-manifest.json`; suite 3199/3199 |
| V. Conventional Commits | PASS | Scoped conventional-commit history; PR #369 title valid `feat(car-002): ...` |
| VI. KISS, Simplicity & YAGNI | PASS | Route→tuple derived not persisted; one canonical snapshot replaced in place; no speculative schema surface |

## Unspecified Implementations

None material. The implementation stayed within the declared file set. The only items
worth naming are additive test hardening the spec anticipated (integrity re-checks,
sanitization re-scan, referential integrity in FR-024) — these are enforcement of
existing requirements, not unspecified scope.

## Task Execution Analysis

- **Completion**: 40/40 tasks (100%). WP1: 18, WP2: 10, WP3: 12. Five `[P]` parallel
  tasks (T022 + the four record-class fixtures T029-T032).
- **Task fidelity**: No tasks dropped or added; all cite FR/SC markers and exact paths;
  no task spans two work packages (CHK034/CHK035 satisfied).
- **TDD**: RED→GREEN followed throughout; the operator live probe (T015) is the single
  non-TDD, human-gated task, exactly as specified (FR-001).
- **Phantom check**: verify-tasks confirmed 40/40 tasks backed by real evidence across
  three detection layers; zero phantom completions.
- **Executor incidents**: 3 checklist-executor + 1 clarify-executor dispatches died on
  API stream timeouts; generation moved to phase-executor with orchestrator-owned
  remediation. All resolutions record-grounded; zero consensus escalations.
- **Rework**: Two re-probes (V1→V2 privacy, V2→V3 classification) and one dead-code fix,
  all pre-merge. No rework leaked past the PR boundary.

## Lessons Learned & Recommendations

Prioritized, tied to findings:

1. **HIGH — Validate committed evidence by re-derivation, not just structure.** The V2
   CAP-Q5 defect passed a green suite because tests never re-derived the outcome from the
   stored raw bytes (SD-2). Recommendation: PSC-1. Durable takeaway: *a green suite does
   not prove committed artifacts are semantically correct.*
2. **HIGH — Teeth-test every declared error disposition.** SD-3's fail-closed path was
   dead code that structural tests never exercised. Recommendation: for each declared
   abort/reject path, assert against a triggering input.
3. **MEDIUM — Sanitization must enumerate every leak class up front.** SD-1 leaked
   session UUIDs because sanitization was scoped to home paths only. Recommendation: when
   a spec says "sanitize machine-local identifiers," enumerate the full class set
   (home/user/session) in the FR and back it with a continuous re-scan (now in place).
4. **MEDIUM — Keep the executor-resilience fallback as a first-class autopilot pattern.**
   The timeout-driven switch to phase-executor kept the run deterministic and
   record-grounded (POS-4). Recommendation: document it as standard degradation behavior.
5. **LOW — Reviewability estimators are blind to test-tree `.py` and `docs/**` JSON.**
   The mechanical estimator projected 0 LOC against a real ~2,236 production reviewable
   LOC. Recommendation: treat the hand estimate as authoritative for such features and
   let the PR-time diff-mode gate arbitrate (already the practice here).

Follow-up commands (operator discretion, none auto-run):
- `/speckit.constitution` — consider POS-1 (re-probe over hand-edit) and POS-2 (surface-
  and-defer) as evidence-integrity / reviewability principle candidates.
- `/speckit.specify` (CAR-003) — carry PSC-1 (outcome re-derivation in consumer
  validation) into the downstream evaluation-runner spec.

## File Traceability Appendix

Production / evidence artifacts (all present, all validated):

| File | Lines | WP | Requirements |
|------|-------|----|--------------|
| docs/ai/research/claude-trace-contract.schema.json | 294 | WP1 | FR-015, FR-016, FR-017, SC-007 |
| docs/ai/research/claude-runtime-capability-snapshot.json (V3) | 249 | WP1 | FR-011, FR-012, FR-013, FR-014, SC-001, SC-004 |
| docs/ai/research/claude-telemetry-capability-profile.json | 134 | WP2 | FR-018, FR-019, FR-020, SC-006 |
| tests/speckit-pro/layer6-efficiency/lib/claude_trace_schema.py | 240 | WP1 | FR-016, FR-028, SC-007 |
| tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py | 1421 | WP1 | FR-001, FR-003, FR-004, FR-005, FR-009, FR-010, FR-012, FR-013, FR-023 |
| tests/speckit-pro/unit/test-efficiency-claude-telemetry.py | 3026 | WP1/2/3 | FR-024, FR-025, FR-002, SC-002, SC-003, SC-005 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/route-resolution.json | 29 | WP2 | FR-021 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/success.json | 41 | WP3 | FR-025, SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/null.json | 41 | WP3 | FR-020, FR-025, SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/unavailable.json | 41 | WP3 | FR-021, FR-025, SC-003 |
| tests/speckit-pro/unit/fixtures/claude-telemetry-records/misdelivery.json | 41 | WP3 | FR-025, SC-003 |
| tests/speckit-pro/suite-manifest.json (modified) | — | WP1 | FR-028 |
| tests/speckit-pro/unit/test-speckit-pro-runner.py (modified) | — | WP1/WP2 | docs-surface guard (FR-011/FR-018) |

Key remediation commits: `1185a3c1` (SD-1 session-UUID redaction, V2), `318087c5`
(SD-2/SD-3 classification + fail-closed fixes), `7f47386a` (V3 re-probe),
`a048dd46` (post-implementation review record).

## Self-Assessment Checklist

| Item | Result | Note |
|------|--------|------|
| Evidence completeness | PASS | Every deviation cites a commit/task/file/behavior |
| Coverage integrity | PASS | All 28 FR + 8 SC IDs enumerated; 0 NFR; none missing |
| Metrics sanity | PASS | completion 40/40=100%; adherence 36/36=100% per the formula |
| Severity consistency | PASS | 0 critical (0 open), 3 significant-resolved, 2 minor, 4 positive |
| Constitution review | PASS | Violations explicitly stated as None (6/6 PASS) |
| Human Gate readiness | PASS | Proposed Spec Changes populated (2); 0 applied; approval required |
| Actionability | PASS | Recommendations prioritized and tied to specific findings |

**Blocking-rule items** (Coverage integrity, Metrics sanity, Human Gate readiness,
Constitution review): all PASS — report finalized.

---

Retrospective saved | Adherence: 100% | Completion: 100% | Critical findings: 0 |
Proposed spec changes: 2 (applied: 0) | Constitution violations: 0

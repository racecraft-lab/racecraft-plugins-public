# Integration Requirements Checklist: Verification Coverage (TACD-004)

**Purpose**: Unit-test the INTEGRATION quality of the TACD-004 requirements — are the
cross-runtime (Claude + Codex) pointer-coverage and target-resolution obligations, the
`dist/claude/**` AND `dist/codex/**` resolution surface, the four-file eval parity, and
the source-derived (never hand-edited) `dist/` rebuild specified completely, clearly,
consistently, and measurably?
**Created**: 2026-06-19
**Domain**: integration
**Depth**: Standard (release-gate; the checks must hold across two runtimes and resolve
against the installed payload, not just source)
**Audience**: Reviewer (PR) + plan author
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `quickstart.md`

> Scope note: This checklist tests the QUALITY OF THE REQUIREMENTS, not the code.
> Each item asks whether an integration concern is specified well enough to implement
> reliably across both the Claude and Codex runtimes.

## Pointer-Coverage Across Both Runtimes (Claude + Codex inventories)

- [ ] CHK001 - Is the pointer-coverage obligation stated for BOTH the Claude agent inventory (`agents/*.md`) AND the Codex agent inventory (`codex-agents/*.toml`), rather than for a single runtime? [Completeness, Spec §FR-003, §FR-009]
- [ ] CHK002 - Is the asymmetry in the pointer FORM across runtimes specified — Claude agents reference the literal `capability-discovery.md` path, while Codex agents may carry the machine-checkable equivalent line ("Capability discovery equivalent: mirrors …/capability-discovery.md …") — so the check applies the right rule per runtime? [Consistency, Spec §FR-009, Assumptions "Approved-equivalent allowlist"]
- [ ] CHK003 - Is the in-scope (capability-dependent) vs out-of-scope agent partition enumerated SEPARATELY for each runtime, given Claude ships 11 agents (incl. `gate-validator`, `consensus-synthesizer`) while Codex ships 10 (no `gate-validator`/`consensus-synthesizer`, plus `autopilot-fast-helper`)? [Completeness, Spec Assumptions "'Active agent' inventory", §FR-003]
- [ ] CHK004 - Is the enumerated exclusion set (agents that perform no capability-dependent work) required to carry a one-line reason EACH, for both runtimes, so "uncovered" is never confused with "out of scope"? [Clarity, Spec §FR-003]
- [ ] CHK005 - Is Claude/Codex parity for pointer-coverage stated as a binding requirement covering the form asymmetry (path vs equivalent line), not just an aggregate "both runtimes are checked" statement? [Consistency, Spec §FR-009]
- [ ] CHK006 - Is the per-runtime agent inventory the pointer check iterates pinned to a deterministic glob (`agents/*.md` and `codex-agents/*.toml`) so a newly added agent in either runtime is automatically in scope rather than silently uncovered? [Coverage, Plan §Source Code, Spec §FR-003]

## Target-Resolution Against Both Built Payload Trees (dist/claude/** AND dist/codex/**)

- [ ] CHK007 - Is it required that target-resolution is verified against `dist/claude/**` AND `dist/codex/**` (both built trees), not merely one runtime's payload? [Completeness, Spec §FR-004, §SC-002]
- [ ] CHK008 - Is failure required for the resolution check when a directive path is correct in source but ABSENT in the built payload, for BOTH runtimes, rather than passing on source-tree presence alone? [Coverage, Spec Edge Case "Unresolved payload path", §US2 AS3/AS4]
- [x] CHK009 - Is the source-path → built-path translation the resolution check must perform specified, given every Claude AND Codex agent references the directive by the repo-root-relative SOURCE path (`speckit-pro/skills/speckit-autopilot/references/capability-discovery.md`) while the file ships under `dist/<runtime>/speckit-pro/skills/.../capability-discovery.md`? Research Decision 3 instead describes resolving a runtime-relative `../references/…` reference, which does not match the actual reference style. [Gap, Spec §FR-004, Research Decision 3] — RESOLVED: FR-004 now defines resolution as the in-source path token re-rooted under each `dist/<runtime>/` tree (`dist/claude/<token>` AND `dist/codex/<token>`), and Research Decision 3 corrected to a prefix re-rooting (no runtime-relative walk; verified zero `../references/` refs across all active agents).
- [ ] CHK010 - Is "the path each runtime loads it from" defined as a computable resolution (a concrete mapping from the in-source reference to the corresponding `dist/<runtime>/**` location), not left as prose, so two implementers derive the same target path? [Clarity, Spec §FR-004, Research Decision 3]
- [ ] CHK011 - Is the dependency that `dist/**` must be committed-in-sync for resolution to be meaningful documented, AND is the check that enforces that sync named (so resolution is not validated against a stale build) for both trees? [Dependency, Research Decision 3, Plan §Declared File Operations]
- [ ] CHK012 - Is the resolution check required to fail for BOTH Claude and Codex layouts when the directive is renamed/removed at a referenced path (the deliberate-regression trigger), rather than passing if only one tree still resolves? [Consistency, Spec §SC-002, §US2 AS4]

## Eval Four-File Parity (autopilot + coach, Claude + Codex)

- [ ] CHK013 - Is the eval rewrite obligation stated for ALL FOUR files explicitly — `evals/speckit-autopilot-evals.json`, `evals/speckit-coach-evals.json`, and both `codex-evals/` counterparts — rather than for "the eval files" generically? [Completeness, Spec §FR-005, Plan §Declared File Operations]
- [ ] CHK014 - Is "Claude/Codex parity" defined as equivalence PER SCENARIO (same optional-tool scenario carries equivalent expectations across runtimes), explicitly NOT equal total eval counts, given the files differ in length (autopilot 26 vs 33 evals; coach 12 vs 14)? [Clarity, Spec §FR-009, §US3 AS2]
- [ ] CHK015 - Is the requirement stated that each rewritten optional-tool expectation asserts BOTH the absence of a named set AND an affirmative capability-first answer identically across the Claude/Codex pair for the same scenario? [Consistency, Spec §FR-005, §US3 AS1/AS2]
- [ ] CHK016 - Is the parity scope bounded to the named skills (autopilot + coach) and required to be mirrored across the `evals/` and `codex-evals/` directories, so a rewrite landing in one tree but not the other is a defined failure? [Coverage, Spec §FR-009, Assumptions "Eval parity scope"]
- [ ] CHK017 - Are the five behavior-observable scenarios (installed-capability discovery, fallback, evidence path, citations/local-file references, lowered confidence) required to be present in BOTH runtimes' eval files in parity, not only the Claude side? [Completeness, Spec §FR-006, §FR-009]
- [ ] CHK018 - Is it required that all four files remain valid JSON parseable by the EXISTING per-runtime eval runners (`run-functional-evals.sh` reads `evals/`; `run-functional-evals-codex.sh` reads `codex-evals/`), so a malformed rewrite cannot break either runner? [Dependency, Research Decision 6, Quickstart §4]

## Source-Derived dist/ Rebuild (never hand-edited)

- [ ] CHK019 - Is the obligation that `dist/**` is regenerated ONLY from source via the build script (never hand-edited) stated as a binding requirement, not just an assumption? [Completeness, Spec §FR-013]
- [ ] CHK020 - Is the source-derived-only rule stated CONSISTENTLY across spec, plan, and quickstart, so a reviewer can reject a hand-edited payload in either the Claude or the Codex tree? [Consistency, Spec §FR-013, Plan §Declared File Operations, Quickstart §2]
- [ ] CHK021 - Is the enforcement mechanism for "committed `dist/**` matches a fresh rebuild" named (the existing `validate-plugin-payload.sh` `git diff --exit-code -- dist`), so the source-derived guarantee is machine-checked and not merely asserted? [Traceability, Research Decision 3, Quickstart §2]
- [ ] CHK022 - Is it specified that BOTH `dist/claude/**` and `dist/codex/**` are regenerated by the same builder run, so the resolution targets in both trees are produced source-derived rather than one tree being maintained by hand? [Coverage, Spec §FR-007, §FR-013, Plan §Project Structure]
- [ ] CHK023 - Is the recovery path for a stale/hand-edited payload specified (re-run `bash scripts/build-plugin-payloads.sh`; payload is forward-only), so a resolution or completeness failure has a defined, source-derived fix? [Recovery, Spec §FR-013, Quickstart §Rollback]

## Cross-Artifact Integration Consistency

- [ ] CHK024 - Do spec, plan, and research AGREE that pointer-coverage + target-resolution live in Layer 1 and the named-tool guard lives in Layer 5, with both runtimes covered, and no conflicting placement statement? [Consistency, Spec §FR-003/§FR-004, Plan §Summary, Research Decisions 2–3]
- [ ] CHK025 - Is each new Layer 1 validator required to be REGISTERED in the suite runner (`tests/speckit-pro/run-all.sh`) so the cross-runtime pointer/resolution checks actually execute in the default run, not merely exist as files? [Completeness, Spec §FR-011, Plan §Declared File Operations]
- [ ] CHK026 - Is fail-closed behavior required for the cross-runtime checks when an input set is empty/missing (e.g., a `codex-agents/*.toml` glob matches nothing, or a referenced `dist/codex/**` target is absent), so a guard cannot pass vacuously on one runtime by examining nothing? [Coverage, Spec §FR-012]
- [ ] CHK027 - Is the assumption validated that the Codex source directive surface (`codex-skills/`) and the Claude source directive (`skills/speckit-autopilot/references/capability-discovery.md`) both feed the builder, so the dist resolution targets in both trees trace to a real source? [Assumption, Spec Assumptions "'Active agent' inventory", Plan §Project Structure]

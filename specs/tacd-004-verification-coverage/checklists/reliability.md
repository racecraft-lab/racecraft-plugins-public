# Reliability Requirements Checklist: Verification Coverage (TACD-004)

**Purpose**: Unit-test the RELIABILITY of the TACD-004 requirements — are the new
guards' non-vacuity, the body-completeness check's determinism, the default-suite
green-without-live-eval guarantee, and the false-positive boundaries specified
completely, clearly, and measurably?
**Created**: 2026-06-19
**Domain**: reliability
**Depth**: Standard (release-gate; the new guards are the load-bearing deliverable)
**Audience**: Reviewer (PR) + plan author
**Source artifacts**: `spec.md`, `plan.md`, `research.md`

> Scope note: This checklist tests the QUALITY OF THE REQUIREMENTS, not the code.
> Each item asks whether something is specified well enough to implement reliably.

## Guard Non-Vacuity (every guard provably fails on a deliberate regression)

- [ ] CHK001 - Is the non-vacuity obligation stated as a binding requirement for EVERY new guard (named-tool guard, pointer-coverage, target-resolution, body-completeness), rather than only as a per-guard aspiration? [Completeness, Spec §FR-012]
- [ ] CHK002 - For the named-tool guard, is the deliberate-regression trigger that MUST cause failure defined concretely (a `mcp__<vendor>__*` token added to an active-agent BODY surface outside the allowlist)? [Clarity, Spec §FR-012, §US1 Independent Test]
- [ ] CHK003 - For pointer-coverage, is the deliberate-regression trigger defined (an active agent that references neither `capability-discovery.md` nor an enumerated equivalent) AND is the required failure output (names the uncovered agent) specified? [Completeness, Spec §US2 AS2, §FR-003]
- [ ] CHK004 - For target-resolution, is the deliberate-regression trigger defined (directive renamed/removed at a referenced path inside the built payload) AND is failure required for BOTH Claude and Codex layouts? [Completeness, Spec §US2 AS4, §SC-002]
- [ ] CHK005 - For body-completeness, is the deliberate-regression trigger defined (a built Claude SKILL.md truncated / trailing heading dropped) AND is the required failure output (names the truncated skill) specified? [Completeness, Spec §US4 AS3, §SC-005]
- [ ] CHK006 - Is there a requirement that reverting each deliberate regression returns the suite to green (the guard does not stay red on legitimate content)? [Coverage, Spec §US1 Independent Test]
- [ ] CHK007 - Is the regression-proof method specified as developer-local and NOT committed (so the deliberate failures never ship in the default suite)? [Clarity, Quickstart §3]

## Named-Tool Guard — False-Positive / False-Negative Boundary (the highest-risk surface)

- [ ] CHK008 - Is the boundary between an ALLOWED concrete tool ID (schema/dependency metadata) and a FLAGGED named-tool preference defined precisely enough to implement deterministically, rather than by the prose phrase "exact schema/dependency metadata identifiers"? [Ambiguity, Spec §FR-001]
- [ ] CHK009 - Do the requirements specify WHICH surfaces the guard scans versus excludes — e.g., Claude frontmatter `tools:` allowlist IDs are metadata (allowed) but agent BODY text is a behavior surface (in scope)? The active agents legitimately carry 8 `mcp__<vendor>__*` IDs in frontmatter `tools:` today. [Completeness, Spec §FR-001; Directive Metadata Policy]
- [ ] CHK010 - Is the "generic `mcp`/`MCP` vocabulary is allowed" rule defined by a checkable property (a bare token with no `__<vendor>__` qualifier) rather than by example alone? [Clarity, Spec §FR-001, Edge Case "Generic mcp vocabulary"]
- [ ] CHK011 - Is the "spike-approved category allowlist" the guard subtracts identified by a concrete, loadable source (path/anchor), so two implementers would derive the same allowlist? [Traceability, Spec Assumptions "Approved category allowlist", §FR-001]
- [ ] CHK012 - Are the legitimate-retention categories enumerated and disjoint (platform schema metadata, dependency metadata, exact file references, fixtures, historical/provenance) so the guard's allow-set is closed and auditable? [Completeness, Spec §US1 AS3, Edge Case "Legitimate concrete identifiers"]
- [ ] CHK013 - Is "active agent" defined unambiguously for the guard's scan scope (the agents shipping in built payloads + their source; excludes archived/historical/provenance), so the guard's input set is deterministic? [Clarity, Spec Assumptions "'Active agent' inventory"]
- [ ] CHK014 - Does the spec require a false-positive regression check (allowed content — generic `mcp`, a frontmatter `tools:` vendor ID — does NOT trip the guard), not only a true-positive one? [Coverage, Spec §US1 AS2/AS3]

## Pointer-Coverage Reliability — the approved-equivalent allowlist must not become a rubber stamp

- [x] CHK015 - The spec assumes the approved-equivalent allowlist is empty "if every active agent references the directive directly," but 5 of 11 Claude agents and 4 of 10 Codex agents do NOT reference `capability-discovery.md`. Is the criterion for what makes an enumerated equivalent LEGITIMATE (vs. an agent simply missing the pointer) specified? [Gap, Spec Assumptions "Approved-equivalent allowlist", §FR-003]
- [x] CHK016 - Is there a requirement that the approved-equivalent allowlist is itself non-vacuous / minimal — i.e., it cannot be silently widened to cover an uncovered agent and thereby defeat the pointer guard? [Gap, Spec §FR-003, §FR-012]
- [ ] CHK017 - For agents that legitimately carry an "approved equivalent," is the machine-checkable form of that equivalent defined (e.g., the Codex agents' literal "Capability discovery equivalent: mirrors …capability-discovery.md" line), so the check stays a literal match and not a heuristic? [Clarity, Spec §FR-003, Edge Case "Approved equivalent pointer"]
- [ ] CHK018 - Is the active-agent inventory the pointer check iterates pinned to a deterministic source (a glob over `agents/*.md` and `codex-agents/*.toml`), so adding a new agent is automatically in scope rather than silently uncovered? [Coverage, Plan §Source Code; Spec §FR-003]
- [ ] CHK019 - Is Claude/Codex parity for pointer-coverage stated as a requirement covering the asymmetry that Claude references the path directly while Codex uses the "equivalent" mirror line? [Consistency, Spec §FR-009]

## Target-Resolution Reliability — must resolve against built payload, not source

- [ ] CHK020 - Is "the path each runtime loads it from" defined as a computable resolution (the referenced relative path resolved from the agent/skill location inside the built tree), not left as prose? [Clarity, Spec §FR-004, Research Decision 3]
- [ ] CHK021 - Is it required that resolution is checked against `dist/claude/**` AND `dist/codex/**` and MUST fail when a path is correct in source but absent in the built payload (not pass on source-tree presence)? [Completeness, Spec Edge Case "Unresolved payload path", §US2 AS3/AS4]
- [ ] CHK022 - Does the spec address the dependency that `dist/**` must be committed-in-sync for the resolution check to be meaningful, and which check enforces that sync (so resolution is not validated against a stale build)? [Dependency, Research Decision 3; Plan §Declared File Operations]

## Body-Completeness Determinism (not flaky across skills)

- [ ] CHK023 - Is the structural-anchor invariant defined precisely ("the last non-guard `##` heading present in source is present in the built payload"), and does it hold given the guard heading is the FIRST section in every SKILL.md so real trailing headings always survive a correct strip? [Clarity, Spec §SC-005, Research Decision 5]
- [x] CHK024 - Is the length-tolerance band specified to be computed PER SKILL from the actual guard-section boundary (source-minus-guard), rather than a single fixed line-count constant that would be flaky across skills of different sizes (source ranges 150–698 lines; guard-section size varies)? [Gap, Spec §FR-008, §SC-005]
- [ ] CHK025 - Is the tolerance "slack" value (how many lines of divergence are permitted) defined and justified, so the band is neither so tight it flakes nor so loose it misses a partial mid-body truncation? [Clarity, Research Decision 5]
- [ ] CHK026 - Is the definition of "the guard section" shared between the `strip_codex_guard` fix and the body-completeness check (same heading→next-`##`/EOF boundary), so the check and the builder cannot disagree on what was stripped? [Consistency, Research Decision 5, §FR-007/§FR-008]
- [ ] CHK027 - Is the no-guard-block edge case covered by a requirement (a SKILL.md with no guard heading is left untouched and still passes completeness)? [Edge Case, Spec Edge Case "Skill with no guard block"]
- [ ] CHK028 - Is the body-completeness check scoped to the surface where the defect occurs (`dist/claude/**`) with an explicit, justified reason it need not also run on `dist/codex/**`? [Clarity, Research Decision 5]
- [ ] CHK029 - Is the check's determinism stated as a requirement (same inputs → same result; no ordering or environment dependence across the skill set)? [Measurability, Spec §FR-010]

## Default-Suite Green Without Live Eval Execution

- [ ] CHK030 - Is it a binding requirement that `bash tests/speckit-pro/run-all.sh` (Layers 1/4/5) passes WITHOUT depending on live AI eval (`claude -p`) execution? [Completeness, Spec §FR-010, §SC-004]
- [x] CHK031 - Is it specified that the new Layer 1 validators are REGISTERED in `run-all.sh` (so they actually run in the default suite, not just exist as files)? The current `run-all.sh` enumerates Layer 1 validators explicitly. [Gap, Plan §Declared File Operations "MODIFIED run-all.sh"]
- [ ] CHK032 - Are the eval-file changes (Layer 3) required to be validated by committed/replay fixtures only, with an explicit statement that NO live run gates merge? [Clarity, Spec §FR-006, §US3 AS3]
- [ ] CHK033 - Is the requirement stated that the four rewritten eval files MUST remain valid JSON and parseable by the existing eval runners (so a malformed rewrite cannot break tooling)? [Completeness, Research Decision 6]
- [ ] CHK034 - Is the "live eval unavailability" edge case covered — when no live runner exists, the default deterministic suite still runs to completion? [Edge Case, Spec Edge Case "Live eval unavailability"]
- [ ] CHK035 - Is there a requirement that the new checks are fast deterministic shell/JSON assertions added only to the existing fast layers (1/4/5), with no new test layer or broad scanner that could change suite runtime/footprint? [Consistency, Spec §FR-011]

## Failure-Mode Diagnostics & Recovery

- [ ] CHK036 - For each guard, is the failure MESSAGE content specified (identifies the offending file/agent/path/skill and token), so a red check is actionable rather than opaque? [Completeness, Spec §US1 AS1, §US2 AS2/AS4, §US4 AS3]
- [ ] CHK037 - Is the recovery path for a body-completeness failure specified (re-run the builder to regenerate `dist/**`; payload is forward-only and never hand-edited)? [Recovery, Spec §FR-013, Quickstart §Rollback]
- [ ] CHK038 - Are the script-safety reliability requirements stated for the new validators (`#!/usr/bin/env bash`, `set -euo pipefail`, quoted vars, `jq` for JSON, passes `bash -n`), so a guard cannot fail-open on a shell error? [Non-Functional, Plan §Constitution Check II]
- [x] CHK039 - Does any requirement guard against a guard that fails OPEN — e.g., an empty active-agent glob, a missing `dist/**` target, or a `jq` parse error silently producing a PASS instead of a FAIL? [Gap, Spec §FR-012]

## Consistency, Assumptions & Cross-Artifact Alignment

- [ ] CHK040 - Do spec, plan, and research agree on guard placement (named-tool guard in Layer 5; pointer/resolution/completeness in Layer 1) with no conflicting statement? [Consistency, Spec §FR-001/§FR-003/§FR-004/§FR-008, Plan §Summary]
- [ ] CHK041 - Is the assumption that the "spike-approved category allowlist" is reused (not redefined) validated against a real, current source the implementer can load? [Assumption, Spec Assumptions "Approved category allowlist"]
- [ ] CHK042 - Is the assumption that `dist/**` is regenerated only from source via the builder (never hand-edited) consistently stated across spec, plan, and quickstart, so a reviewer can reject a hand-edited payload? [Consistency, Spec §FR-013, Plan, Quickstart §2]

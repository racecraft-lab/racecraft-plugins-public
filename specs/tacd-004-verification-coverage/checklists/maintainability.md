# Maintainability Requirements Checklist: Verification Coverage (TACD-004)

**Purpose**: Unit-test the MAINTAINABILITY of the TACD-004 requirements — are the
`strip_codex_guard` fix's minimality and focused coverage, the surgical removal of the
named-tool assertions (without disturbing unrelated Layer 5 expectations), the
minimality/auditability of the approved-equivalent allowlist, and the no-scope-drift
boundary (no agent-behavior or shipped-docs-wording changes) specified completely,
clearly, and consistently?
**Created**: 2026-06-19
**Domain**: maintainability
**Depth**: Standard (release-gate; a shared build script and the tool-scoping contract
are high-blast-radius surfaces — every install consumer receives the change)
**Audience**: Reviewer (PR) + plan author
**Source artifacts**: `spec.md`, `plan.md`, `research.md`, `quickstart.md`

> Scope note: This checklist tests the QUALITY OF THE REQUIREMENTS, not the code.
> Each item asks whether something is specified well enough to be maintained safely on
> a high-blast-radius surface, without scope drift or collateral breakage.

## strip_codex_guard — Minimal Section-Boundary Change

- [ ] CHK001 - Is the `strip_codex_guard` fix specified as a localized section-boundary change (strip from the `## Codex Skill-Selection Guard` heading to the next `## ` heading or EOF), explicitly scoped to that one function rather than a broader builder refactor? [Clarity, Spec §FR-007, Research Decision 4]
- [ ] CHK002 - Is the requirement explicit that the ONLY intended source→built difference is the stripped guard section (no other builder behavior — copy lists, manifest rewrite, path rewrite — is changed)? [Completeness, Spec §FR-007, Plan §Summary item 3]
- [ ] CHK003 - Is the collapse of the existing trailing special-case block (the "The Codex variant must…" handling) into the single section-boundary rule called out, with the requirement that it not change output for the one skill that contains that block (`speckit-autopilot/SKILL.md`)? [Coverage, Research Decision 4; Edge Case "Skill with no guard block"]
- [ ] CHK004 - Is the no-guard-block case specified as a no-op for the fixed function (a SKILL.md without the guard heading is left byte-for-byte untouched), so the change does not regress skills that never had a guard? [Edge Case, Spec Edge Case "Skill with no guard block", Research Decision 4]
- [ ] CHK005 - Is the rejected alternative (un-wrapping the terminator phrase in source SKILL.md files) documented as out of scope because it would touch shipped guidance wording, so the fix stays confined to the builder? [Traceability, Research Decision 4; Spec Out of Scope]

## strip_codex_guard — Its Own Focused Coverage (not folded into an unrelated check)

- [ ] CHK006 - Is the body-completeness check specified as the dedicated, focused coverage for the `strip_codex_guard` fix (a deliberately truncated built SKILL.md MUST make it FAIL and name the skill), rather than the fix relying only on the broad `git diff -- dist` sync check? [Completeness, Spec §FR-008, §SC-005, Research Decision 5]
- [ ] CHK007 - Is the "guard section" boundary definition required to be SHARED between the fixed `strip_codex_guard` and the body-completeness check (same heading→next-`##`/EOF boundary), so the fix and its coverage cannot drift apart over time? [Consistency, Spec §FR-008, Research Decisions 4–5]
- [ ] CHK008 - Is the body-completeness coverage scoped to exactly the surface the fix touches (`dist/claude/**`), with a stated, justified reason it need not also run on `dist/codex/**`, so the coverage is targeted and not over-broad? [Clarity, Research Decision 5]
- [ ] CHK009 - Is the focused-coverage placement constrained to the existing fast layers (a Layer 1 validator), with no new test layer introduced for the payload fix? [Consistency, Spec §FR-011]

## Named-Tool Assertion Removal — Surgical, No Collateral Breakage

- [ ] CHK010 - Is the removal scoped precisely to the single Layer 5 location that names the vendor MCP set (the `implement-executor` research-capability loop asserting `mcp__tavily-mcp__*` / `mcp__context7__*` / `mcp__RepoPrompt__*`), so the edit is surgical within `validate-tool-scoping.sh`? [Clarity, Spec §FR-002, Research Decision 1]
- [ ] CHK011 - Is it specified that removing the named set MUST NOT disturb the unrelated Layer 5 expectations in the same file — the per-agent `assert_no_mcp_tools` checks, the universal single-orchestrator denial loop (no `Agent`/`TeamCreate`/`SendMessage`), and the Codex sandbox-mode/model/effort scoping? [Completeness, Spec §FR-002; Layer 5 unrelated assertions]
- [ ] CHK012 - Is the post-removal expectation for `implement-executor` stated (it retains its generic research capability `WebSearch`/`WebFetch` and is NOT switched to a blanket `assert_no_mcp_tools`, since its frontmatter still legitimately grants vendor MCP tools), so the rework does not over-correct into a new false contract? [Clarity, Spec §FR-002, Research Decision 1]
- [ ] CHK013 - Does any requirement establish that the named-tool guard scans only the behavior surface (agent BODY prose) and EXCLUDES the frontmatter `tools:` grant list, given active agents legitimately carry vendor `mcp__*` IDs in frontmatter (codebase-analyst, analyze-executor, clarify-executor, implement-executor) but none in body — so the new guard does not force collateral edits to those frontmatter grants? [Completeness, Spec §FR-001; agent-frontmatter metadata policy]
- [ ] CHK014 - Is the boundary between the REMOVED named assertions (Layer 5 contract) and the ADDED named-tool guard (Layer 5 regression scanner) specified so the two do not overlap or contradict (removal frees the contract; the guard prevents re-introduction in body prose)? [Consistency, Spec §FR-001/§FR-002, Research Decision 1]

## Approved-Equivalent Allowlist — As Small As The Inventory Requires

- [ ] CHK015 - Is the approved-equivalent allowlist required to be kept as small as the actual capability-dependent agent inventory requires, with the empty-set default stated when every covered agent references `capability-discovery.md` directly? [Clarity, Spec Assumptions "Approved-equivalent allowlist", §FR-003]
- [ ] CHK016 - Is the legitimacy criterion for an allowlist entry specified (an entry is valid only when the agent demonstrably carries the capability-first guidance in a machine-checkable form — the Codex "Capability discovery equivalent: mirrors …capability-discovery.md" line — NOT merely to silence an in-scope agent missing the pointer)? [Clarity, Spec Assumptions "Approved-equivalent allowlist", §FR-012]
- [ ] CHK017 - Is the allowlist required to be a LITERAL enumeration in the validator (not a heuristic / pattern), and explicitly NOT widenable to turn a red check green, so it stays auditable and minimal as agents change? [Consistency, Spec §FR-003, Assumptions "Approved-equivalent allowlist"]
- [ ] CHK018 - Is the out-of-scope exclusion set required to be a literal enumeration with a one-line reason per agent, kept distinct from the equivalent-allowlist, so the maintainer can tell "covered via equivalent" apart from "intentionally excluded" without re-deriving either? [Clarity, Spec §FR-003]
- [ ] CHK019 - Is there a stated maintenance rule that a newly added capability-dependent agent is automatically in scope (via the `agents/*.md` / `codex-agents/*.toml` glob) and must EITHER gain the pointer OR be added to the exclusion set — never be silently absorbed by widening the equivalent-allowlist? [Coverage, Spec §FR-003, Plan §Source Code]

## No Scope Drift — Verification + Payload Build Only

- [ ] CHK020 - Is the no-scope-drift boundary stated as a binding constraint — no agent decision-logic changes, no prerequisite-script behavior changes, no shipped-docs wording changes — rather than only as background context? [Completeness, Spec Out of Scope, Assumptions "No behavior, prerequisite, or docs changes"]
- [x] CHK021 - Is the distinction between the IN-SCOPE secondary surface (spec/workflow process artifacts under `docs/process`) and the OUT-OF-SCOPE shipped-guidance wording (the directive `capability-discovery.md`, agent bodies, SKILL.md prose) drawn explicitly, so "docs" edits cannot quietly drift into shipped guidance? [Gap, Spec §Reviewability Budget, Out of Scope]
- [ ] CHK022 - Is `capability-discovery.md` explicitly designated as referenced/read-only by the new checks (a resolution target, never an edit target), so the pointer/resolution work cannot drift into rewording the directive it validates? [Clarity, Plan §Project Structure "directive (referenced, not edited)"]
- [ ] CHK023 - Is it specified that the named-tool guard MUST NOT rewrite or flag historical/provenance or generated source-derived mentions of named tools (only NEW hardcoded preferences in active body guidance), so enforcement does not drift into churning legacy content? [Coverage, Spec §US1 AS3, Out of Scope, Edge Case "Legitimate concrete identifiers"]
- [x] CHK024 - Is the eval rewrite (FR-005) bounded to the four named eval fixtures and explicitly excluded from being an agent-behavior change, so rewriting expected outputs is not mistaken for editing what the agents actually do? [Gap, Spec §FR-005, Assumptions "No behavior, prerequisite, or docs changes"]

## Change Footprint, Reversibility & Cross-Artifact Alignment

- [ ] CHK025 - Is the production-change footprint pinned to exactly one production file (`scripts/build-plugin-payloads.sh`) with the test/validator and eval edits enumerated, so the high-blast-radius surface is bounded and reviewable? [Completeness, Spec §Reviewability Budget, Plan §Declared File Operations]
- [ ] CHK026 - Is the option to combine the pointer-coverage and target-resolution validators into one file (when small enough) specified as LOC-neutral, so the maintainer can choose the cleaner surface without changing scope? [Clarity, Plan §Declared File Operations note]
- [ ] CHK027 - Is each new Layer 1 validator required to be REGISTERED in `tests/speckit-pro/run-all.sh` (which enumerates Layer 1 validators explicitly), so a maintained-but-unwired validator is a defined failure rather than silent dead code? [Completeness, Spec §FR-011, Plan §Declared File Operations]
- [ ] CHK028 - Is the rollback/reversibility story specified for the high-blast-radius change (the payload fix is forward-only — re-running the builder restores bodies — and the PR is revert-clean with no destructive migration)? [Recovery, Quickstart §Rollback, §PR packet "Rollback / flags"]
- [ ] CHK029 - Do spec, plan, research, and quickstart agree on the surface map (Layer 5 = named-tool guard + named-set removal; Layer 1 = pointer/resolution/completeness; `scripts/` = strip fix; eval files = behavior expectations) with no conflicting placement that would confuse future maintenance? [Consistency, Spec §FR-001/§FR-003/§FR-004/§FR-008, Plan §Summary, Research Decisions 1–6]
- [ ] CHK030 - Are the script-safety conventions for the new/edited validators stated (`#!/usr/bin/env bash`, `set -euo pipefail`, quoted vars, `jq` for JSON, `chmod +x`, passes `bash -n`) so they match the existing harness style and stay maintainable alongside their siblings? [Non-Functional, Plan §Constitution Check II, Quickstart §5]

## Notes

- Check items off as completed: `[x]`
- A gap-marked item flags a requirement-quality gap surfaced by this domain; when
  resolved, the underlying spec/plan is edited and the item is marked `[x]` with its
  `[Gap, refs]` annotation preserved as provenance plus a `— RESOLVED:` note.
- Traceability: ≥80% of items carry a `[Spec §…]` / `[Research …]` / `[Plan …]` ref or a
  gap / assumption marker.

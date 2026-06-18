# PRD: Tool-Agnostic Capability Discovery for SpecKit Pro

**Status**: Draft
**Source**: Interactive `speckit-prd` + `grill-me` session on 2026-06-17
**Created**: 2026-06-17
**Last updated**: 2026-06-18
**Target window**: Next SpecKit Pro roadmap slot after DOC-006 archive
**Spec ID prefix**: `TACD-###` (Tool-Agnostic Capability Discovery)

---

## 1. Problem

> "SpecKit Pro should not tell orchestrating agents which optional research or context tools to prefer; it should tell them how to discover and use the best capabilities the user actually installed."

Today, active SpecKit Pro agent guidance, prerequisite messaging, and evals name a small set of optional MCP tools as preferred enhancements. That creates a product bias toward those tools, even though users may have different context-management, research, library-documentation, web-search, installed-skill, or repo-local helper capabilities available.

The user-facing behavior should shift from "these named optional MCPs improve the autopilot" to "agents discover installed capabilities by need, use the best available option, and fall back transparently when evidence quality is lower."

## 2. Goals & Non-goals

### 2.1 Goals

- Remove named optional MCP preferences from active SpecKit Pro runtime guidance, prerequisite messaging, documentation, and eval expectations.
- Define a capability-first discovery contract for orchestrating agents and phase agents.
- Let agents consider native tools, MCP/app connectors, installed skills/plugins, and repo-local helpers before using generic fallbacks.
- Preserve backward compatibility for users who already have formerly named tools installed by allowing discovery to select them when they are exposed as the best available capability.
- Require lightweight evidence in agent output: capability path used, citations or local file references, and confidence when fallback quality is lower.
- Verify the behavior with both deterministic static checks and functional evals.

### 2.2 Non-goals (out of scope)

- Bundling, installing, or recommending replacement third-party MCP servers.
- Creating a universal discovery framework for every possible agent runtime outside Claude Code and Codex.
- Replacing the existing SpecKit Pro consensus architecture.
- Guaranteeing that every user-installed tool or skill can be used from every subagent context.
- Removing historical references from changelogs, archive reports, or intentionally historical fixtures.

## 3. Acceptance Criteria

### 3.1 Platform Mechanics Spike *(-> TACD-001)*

- **AC-1.1**: A spike report audits the current Claude and Codex runtime surfaces that reference optional research/context tools, including agent definitions, skill references, prerequisite checks, plugin limitation docs, and tests/evals.
- **AC-1.2**: The spike verifies how each runtime can direct agents to discover and use installed tools, MCP/app connectors, skills/plugins, and repo-local helpers without hardcoding a vendor-specific MCP list.
- **AC-1.3**: The spike recommends the directive home: a shared capability-discovery reference with runtime-specific pointers and approved equivalents, backed by deterministic pointer checks and behavior-observable evals.
- **AC-1.4**: The spike identifies exact file categories where historical named-tool references may remain, and where active guidance must become vendor-neutral.

### 3.2 Capability Discovery Directive and Agent Updates *(-> TACD-002)*

- **AC-2.1**: Active Claude and Codex agent guidance uses capability categories rather than named optional MCP tools for codebase context, spec context, library documentation, web/domain research, source extraction, installed skills/plugins, and repo-local helpers.
- **AC-2.2**: Relevant orchestrating and phase agents follow the same directive home or equivalent spike-approved structure.
- **AC-2.3**: Agents first choose the best installed capability for the task, then fall back to local/platform capabilities when no installed option is available.
- **AC-2.4**: Agent outputs that depend on research or context discovery include the capability path used, citations or local file references, and confidence level.
- **AC-2.5**: Existing users with formerly named tools installed can still benefit through discovery, but those tools are no longer privileged in active guidance.

### 3.3 Prerequisite and Documentation Messaging *(-> TACD-003)*

- **AC-3.1**: The autopilot prerequisite check replaces the hardcoded optional MCP server report with a generic, non-blocking capability advisory.
- **AC-3.2**: User-facing docs and coaching references explain that SpecKit Pro is tool-agnostic for research/context capabilities and degrades gracefully when fewer capabilities are installed.
- **AC-3.3**: Active guidance names capabilities, not tool IDs, except where a platform schema or exact file reference requires a concrete identifier.
- **AC-3.4**: Missing optional capabilities do not fail prerequisites; they only lower evidence confidence or require user escalation when no acceptable fallback exists.

### 3.4 Verification Coverage *(-> TACD-004)*

- **AC-4.1**: Deterministic tests fail if active runtime guidance reintroduces a hardcoded named-tool contract outside the spike-approved historical allowlist.
- **AC-4.2**: Structural or tool-scoping tests verify that relevant Claude and Codex agents point to the approved capability-discovery directive or carry its approved equivalent.
- **AC-4.3**: Functional evals prove that SpecKit Pro answers optional-tool questions in vendor-neutral terms and describes installed-capability discovery plus fallback behavior.
- **AC-4.4**: The default deterministic suite passes: `bash tests/speckit-pro/run-all.sh`.

## 4. Migration Path (phased - one phase per SPEC)

- **Phase 1 (TACD-001) - Platform Mechanics Spike**: Verify runtime mechanics, directive-home feasibility, and testability before editing shipped behavior.
- **Phase 2 (TACD-002) - Capability Directive and Agent Updates**: Apply the spike decision to active agent instructions across Claude and Codex.
- **Phase 3 (TACD-003) - Prerequisite and Documentation Messaging**: Replace setup/user-facing hardcoded MCP guidance with a generic capability advisory.
- **Phase 4 (TACD-004) - Verification Coverage**: Update deterministic checks and evals so the vendor-neutral contract stays enforced.

## 5. Constraints

- Follow the Racecraft Plugins Public constitution: KISS, no speculative abstractions, structural compliance, script safety, and tests before merge.
- Keep the change scoped to `speckit-pro/` and `tests/speckit-pro/` unless the spike proves a repo-level docs/index update is required.
- Do not edit plugin versions manually; release-please owns version changes.
- Do not remove historical archive/changelog provenance solely to satisfy wording preferences.
- Keep deterministic tests shell-based and aligned with existing Layer 1, Layer 4, and Layer 5 patterns.

## 6. Decisions and Open Questions

- **Resolved (TACD-001):** Use a shared capability-discovery reference with runtime-specific pointers and approved equivalents across Claude and Codex. TACD-004 must prove static pointer coverage, target resolution, and behavior-observable eval scenarios before the contract is considered enforced.
- **Resolved (TACD-001):** Separate named optional-tool references by category, not by a broad string ban. Active runtime guidance is blocked after TACD-002, prerequisite/user-facing messaging is blocked after TACD-003, deterministic/eval expectations are blocked after TACD-004, and historical/provenance or generated source-derived duplicates may remain when clearly classified.
- **Open (TACD-002/TACD-004):** Exact runtime/dependency metadata IDs may remain where platform schema or dependency declaration requires them, unless TACD-002 proves an equivalent generic declaration path and TACD-004 can enforce it.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Platform Mechanics Spike | AC-1.* | TACD-001 | - | P1 |
| Capability Discovery Directive and Agent Updates | AC-2.* | TACD-002 | TACD-001 | P1 |
| Prerequisite and Documentation Messaging | AC-3.* | TACD-003 | TACD-001, TACD-002 | P1 |
| Verification Coverage | AC-4.* | TACD-004 | TACD-001, TACD-002, TACD-003 | P1 |

## 8. Success Criteria

1. Active SpecKit Pro guidance no longer presents a named optional MCP set as preferred or expected.
2. Claude and Codex agents share the same installed-capability discovery contract or a spike-approved equivalent.
3. Users without optional research/context tools can still run autopilot with transparent fallback confidence.
4. Users with formerly named tools installed can still benefit when discovery selects those capabilities.
5. Static checks and functional evals pass and protect the vendor-neutral contract from regression.

## 9. References

- **Design concept:** `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md`
- **Technical roadmap:** `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/tool-agnostic-capability-discovery-roadmap-MOC.md`
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `CLAUDE.md`

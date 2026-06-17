---
topic: "Tool-agnostic capability discovery for SpecKit Pro"
slug: "tool-agnostic-capability-discovery"
date: "2026-06-17"
mode: "standalone"
source_input:
  type: "topic"
  ref: "Remove optional named MCP tool opinions from SpecKit Pro and replace them with installed-capability discovery plus fallback behavior."
question_count: 14
stop_reason: "natural"
---

# Design Concept: Tool-Agnostic Capability Discovery for SpecKit Pro

> **Source:** Remove optional named MCP tool opinions from SpecKit Pro and replace them with installed-capability discovery plus fallback behavior.
> **Date:** 2026-06-17
> **Questions asked:** 14
> **Stop reason:** natural

## Goals

- Make SpecKit Pro vendor-neutral across active Claude and Codex runtime guidance, prerequisites, docs, and tests.
- Replace named optional MCP preferences with a capability-first discovery contract.
- Let orchestrating agents consider native tools, MCP/app connectors, installed skills/plugins, and repo-local helpers before falling back.
- Preserve benefit for users who already installed formerly named tools by allowing discovery to select them when they are the best available capability.
- Require lightweight evidence for tool choices: capability path, citations or local files, and confidence level.
- Verify the behavior with both deterministic checks and functional evals.

## Non-goals

- Bundling or requiring new MCP servers, connectors, or skills.
- Creating a generic marketplace installer for third-party research or context tools.
- Replacing the existing consensus architecture.
- Guaranteeing that every possible user-installed tool can be invoked by every runtime.
- Removing historical mentions from changelogs, archive reports, or intentionally historical fixtures.

## Design Tree (Q&A log)

### Q1. Which shipped surfaces should this PRD require the tool-agnostic directive to cover?

**Branch:** Scope

**Recommended answer:** Claude + Codex + tests
> The repo contains current named-tool references in both Claude Markdown agents and Codex TOML agents, plus tests/evals that expect those names. Covering only one runtime would leave the plugin behavior inconsistent.

**Alternatives offered:**
- Codex first: Targets Codex agent TOML and Codex skill docs first; Claude Markdown agents remain for a later compatibility pass.
- Docs only: Changes user-facing guidance and prerequisite messaging without changing agent allowlists or eval expectations yet.

**User's answer:** Claude + Codex + tests

---

### Q2. How should the new directive define tool choice for orchestrating agents?

**Branch:** Capability model

**Recommended answer:** Capability-first discovery
> A capability model removes vendor preference while staying actionable: agents decide whether they need codebase context, library docs, web search, extraction, or research synthesis, then choose the best available installed option.

**Alternatives offered:**
- Full inventory first: Agents enumerate every installed tool/skill before work begins, which is thorough but slower and noisier.
- Fixed fallback chain: Keeps a predefined order but still leaves SpecKit Pro somewhat opinionated.

**User's answer:** Capability-first discovery

---

### Q3. What should happen when no installed tool or skill covers a needed research capability?

**Branch:** Fallback behavior

**Recommended answer:** Use built-ins and flag confidence
> This preserves autopilot progress without pretending the evidence quality is unchanged. It also matches the current plugin posture that missing optional tools should not block work.

**Alternatives offered:**
- Ask user to install tools: Safer for evidence quality but interrupts autopilot.
- Skip that research: Maximizes progress but risks weak or stale decisions.

**User's answer:** Use built-ins and flag confidence

---

### Q4. Should active SpecKit Pro guidance continue naming Tavily, Context7, or RepoPrompt as examples?

**Branch:** Vendor neutrality

**Recommended answer:** Remove from active guidance
> Active guidance should express capabilities, not vendor names. Historical material can keep old names where needed for traceability.

**Alternatives offered:**
- Allow neutral examples: Clearer for current users but keeps visible vendor bias.
- Keep optional-tool docs: Smallest scope but does not fully solve the opinionated-tool problem.

**User's answer:** Remove from active guidance

---

### Q5. Should the roadmap start with a research spike to verify how Claude and Codex agents can discover and use installed tools/skills dynamically?

**Branch:** Platform risk

**Recommended answer:** Yes, spike first
> Claude and Codex expose agent/tool configuration differently. A spike prevents rework before changing allowlists, installer docs, or eval expectations.

**Alternatives offered:**
- No, implement directly: Faster but higher platform-risk rework.
- Codex spike only: Focuses on the current runtime but leaves Claude parity unresolved.

**User's answer:** Yes, spike first

---

### Q6. Which SPEC catalog shape should the PRD use?

**Branch:** Feature breakdown

**Recommended answer:** Four slices
> The repo scan suggests four reviewable vertical slices: platform spike, agent directive updates, prerequisite/docs messaging, and verification coverage.

**Alternatives offered:**
- Three slices: Smaller roadmap but denser implementation PRs.
- One broad spec: Faster to describe but too large for reviewability.

**User's answer:** Four slices

---

### Q7. What should count as an installed capability that agents must consider?

**Branch:** Capability inventory

**Recommended answer:** Tools, MCPs, skills, local helpers
> This matches the requested direction and keeps agents from ignoring useful repo-native scripts or installed skill workflows.

**Alternatives offered:**
- Tools and MCPs only: Simpler but misses installed skills and repo helpers.
- Skills first: Higher-level, but may ignore precise low-level research tools.

**User's answer:** Tools, MCPs, skills, local helpers

---

### Q8. Where should the tool-discovery directive live?

**Branch:** Directive home

**Recommended answer:** Shared reference plus pointers
> A single reference prevents drift across Claude and Codex agents, but only if tests can reliably prove the pointers and behavior remain intact.

**Alternatives offered:**
- Inline every agent: Self-contained but repetitive and drift-prone.
- Autopilot skill only: Smaller, but phase agents may retain stale behavior.

**User's answer:** Shared reference if evals can verify and validate that it works every time; otherwise the spike should research the best option.

---

### Q9. What verification bar should the PRD require for the vendor-neutral directive?

**Branch:** Verification

**Recommended answer:** Static + eval coverage
> Deterministic checks can prove active named-tool contracts do not remain, while functional evals prove agents explain and apply capability discovery.

**Alternatives offered:**
- Static tests only: Reliable but may miss behavior regressions.
- Evals only: Direct behavior validation, but slower, costlier, and less deterministic.

**User's answer:** Static + eval coverage

---

### Q10. What evidence should agents report when they choose research/context tools?

**Branch:** Evidence

**Recommended answer:** Capability used + confidence
> This keeps outputs readable while making fallback quality visible to users and reviewers.

**Alternatives offered:**
- Full tool inventory log: More auditable but noisy and brittle.
- No extra evidence: Shorter output but opaque.

**User's answer:** Capability used + confidence

---

### Q11. How should the existing MCP prerequisite check change?

**Branch:** Prerequisites

**Recommended answer:** Replace with generic capability advisory
> This removes hardcoded vendor checks while preserving a useful non-blocking installation-health signal.

**Alternatives offered:**
- Delete the check entirely: Least opinionated but less helpful.
- Keep but rename optional: Smallest code change but keeps old tool choices baked in.

**User's answer:** Replace with generic capability advisory

---

### Q12. May active guidance name platform-native fallback tools such as local search/read or built-in web search/fetch?

**Branch:** Wording

**Recommended answer:** Name capabilities, not tool IDs
> Capability wording stays vendor-neutral while still giving agents enough direction to choose a local or platform-native fallback.

**Alternatives offered:**
- Name native tools explicitly: Clearer but runtime-specific.
- Avoid all fallback names: Most neutral but too vague.

**User's answer:** Name capabilities, not tool IDs

---

### Q13. Should users who already have Tavily, Context7, or RepoPrompt installed still benefit from them after this change?

**Branch:** Backward compatibility

**Recommended answer:** Yes, via discovery
> The plugin stops naming or requiring specific tools, but discovery can still select them if the user's runtime exposes them as the best available capability.

**Alternatives offered:**
- No preference: Only promises capability discovery.
- No, avoid them: Removes bias but may reduce quality for users who intentionally installed them.

**User's answer:** Yes, via discovery

---

### Q14. What execution order should the roadmap use for the four SPECs?

**Branch:** Sequencing

**Recommended answer:** Spike, directive, messaging, tests
> This buys down platform risk first, then changes behavior, updates user-facing messaging, and locks the result with tests.

**Alternatives offered:**
- Spike, tests, directive, messaging: More TDD-oriented but may churn if the directive shape changes.
- Parallel after spike: Faster but needs tighter coordination.

**User's answer:** Spike, directive, messaging, tests

## Open Questions

- **What:** Whether a shared reference plus pointers can be verified strongly enough across Claude and Codex agents.
  **Why deferred:** The user accepted the shared-reference approach only if evals can validate it reliably.
  **Suggested next step:** Resolve in TACD-001 with a short platform mechanics spike.

- **What:** Exact allowlist/exclusion rules for deterministic tests that ban active named-tool contracts while preserving historical references.
  **Why deferred:** Requires auditing current file categories and fixtures.
  **Suggested next step:** Define in TACD-004 after TACD-001 establishes the directive home.

## Recommended Next Step

Use the companion PRD and technical roadmap, then run `$speckit-scaffold-spec TACD-001` to prepare the platform spike.

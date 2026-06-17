# Tool-Agnostic Capability Discovery Spike

## Summary

TACD-001 is a report-only spike for deciding how SpecKit Pro should move from named optional MCP preferences to installed-capability discovery. The evidence supports this split:

- TACD-002 should update active Claude and Codex runtime guidance to choose by capability, not by named optional tool.
- TACD-003 should replace prerequisite and user-facing setup language with a generic non-blocking capability advisory.
- TACD-004 should add deterministic checks plus functional eval scenarios after TACD-002 and TACD-003 define the final active guidance.

The recommended directive home is a shared capability-discovery reference with runtime-specific pointers and approved equivalents. This is valid only if TACD-004 adds static pointer coverage and behavior-observable eval scenarios for both Claude Code and Codex.

## Scope And Non-Goals

This report follows the TACD roadmap slice for `TACD-001`: verify Claude and Codex discovery mechanics, audit current optional-tool references, decide the directive home, and hand off the behavior changes to later specs. The roadmap explicitly calls this a spike that should not directly rewrite shipped agent behavior. Evidence: `docs/ai/specs/tool-agnostic-capability-discovery-technical-roadmap.md:93-106`.

Non-goals for this slice:

- no agent guidance rewrite
- no prerequisite script or public docs behavior change
- no generated payload semantic change
- no final TACD-004 enforcement tests or eval updates
- no raw runtime inventory, transcript, connector list, session ID, request ID, access token, or absolute machine path in committed evidence

The design concept requires a capability-first direction, including native tools, MCPs, skills, and local helpers, while preserving benefit for users who already have formerly named tools installed. Evidence: `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:20-27`, `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:129-140`, and `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:219-224`.

## Evidence States And Confidence

Evidence states used below:

- `source-backed`: local repo source directly supports the claim.
- `probe-backed`: a local command result supports the claim.
- `environment-specific`: runtime behavior depends on the user's installed tools or parent-session configuration.
- `unsupported`: source or probe evidence shows the capability is not available on that surface.
- `unresolved`: source/probe evidence is insufficient and a later spec or reviewer decision is needed.

Confidence values:

- `high`: direct active source or reproducible probe evidence with no known conflict.
- `medium`: source evidence is indirect, template-only, configuration-dependent, or not end-to-end runtime proof.
- `low`: evidence is incomplete, ambiguous, or known to require a downstream decision.

## Local Source Inventory

The inventory used local source commands only:

```bash
rg -n "Tavily|tavily|Context7|context7|RepoPrompt|repoprompt|MCP|mcp" speckit-pro tests/speckit-pro docs -S
rg -n "capability|capabilities|installed tool|app connector|MCP|mcp" speckit-pro tests/speckit-pro docs -S
find speckit-pro/agents speckit-pro/codex-agents -maxdepth 1 -type f | sort
find dist/claude/speckit-pro dist/codex/speckit-pro -maxdepth 3 -type f | sort
```

Sanitized command results:

- Active Claude/Codex agent source files counted: 21.
- Generated Claude/Codex payload files counted: 54.
- Files matching named optional-tool terms across `speckit-pro`, `tests/speckit-pro`, and `docs`: 59.
- Files matching capability/discovery terms across the same roots: 84.

These counts are evidence of breadth, not a committed raw inventory. The detailed classifications below cite representative active surfaces and hand off broader enforcement to TACD-004.

## Audit Inventory

| Surface | Example Evidence | Category | TACD Owner | Recommendation |
|---------|------------------|----------|------------|----------------|
| Claude codebase analyst agent | `speckit-pro/agents/codebase-analyst.md:12-20`, `speckit-pro/agents/codebase-analyst.md:54-67` | active runtime guidance | TACD-002 | Replace preferred named RepoPrompt wording with capability-first codebase-context discovery; preserve fallback behavior. |
| Claude domain researcher agent | `speckit-pro/agents/domain-researcher.md:11-18`, `speckit-pro/agents/domain-researcher.md:53-67` | active runtime guidance | TACD-002 | Replace preferred Tavily/Context7 wording with web-search, extraction, and library-doc capability categories. |
| Claude implement executor | `speckit-pro/agents/implement-executor.md:103-127` | active runtime guidance | TACD-002 | Replace concrete research-tool preference order with capability categories and evidence reporting. |
| Codex codebase analyst agent | `speckit-pro/codex-agents/codebase-analyst.toml:35-52` | active runtime guidance | TACD-002 | Replace RepoPrompt-specific preference language with codebase-context capability discovery. |
| Codex domain researcher agent | `speckit-pro/codex-agents/domain-researcher.toml:33-49` | active runtime guidance | TACD-002 | Replace Tavily/extract/Context7-specific wording with generic research and docs capabilities. |
| Codex implement executor | `speckit-pro/codex-agents/implement-executor.toml:69-99` | active runtime guidance | TACD-002 | Replace named tool order with capability order plus confidence/citation evidence. |
| Prerequisite script | `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh:115-142` | prerequisite/user-facing messaging | TACD-003 | Replace hardcoded named MCP set with a generic capability advisory. |
| Plugin limitation docs | `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:30-38`, `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:66-86` | prerequisite/user-facing messaging | TACD-003 | Keep non-blocking caveat, but describe capability classes instead of the fixed vendor list. |
| Codex dependency metadata | `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16` | runtime/dependency metadata | TACD-002/TACD-004 | Exact metadata IDs may remain until TACD-001/TACD-002 prove equivalent Codex discovery or dependency declaration behavior. |
| Layer 3 eval expectations | `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:107-116`, `tests/speckit-pro/layer3-functional/codex-evals/speckit-autopilot-evals.json:112-120` | deterministic/eval expectation | TACD-004 | Rewrite eval expected output only after runtime guidance and prerequisite wording change. |
| Layer 5 tool scoping | `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh:240-250` | deterministic/eval expectation | TACD-004 | Keep until TACD-004 defines approved directive-pointer checks and named-tool allowlists. |
| Generated Claude payload | `dist/claude/speckit-pro/agents/codebase-analyst.md:12-20`, `dist/claude/speckit-pro/agents/codebase-analyst.md:52-67` | generated source-derived duplicate | TACD-002/release | Do not edit directly in TACD-001; regenerate after source guidance changes. |
| Generated Codex payload | `dist/codex/speckit-pro/codex-agents/codebase-analyst.toml:35-52` | generated source-derived duplicate | TACD-002/release | Do not edit directly in TACD-001; regenerate after source guidance changes. |
| PRD/design/roadmap mentions | `docs/prd-tool-agnostic-capability-discovery.md:16-28`, `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:20-27` | historical/planning provenance | TACD-004 | Keep as provenance unless TACD-004 finds active guidance masquerading as history. |

Ambiguous references should use `ambiguous/requires-review`, `allowed_status: review`, low confidence, candidate categories, missing evidence, and a named owner. No ambiguous reference should be silently treated as active guidance or historical provenance.

## Platform Mechanics Matrix

| Runtime | Capability | Evidence State | Confidence | Evidence And Rationale | Absent-Capability Disposition |
|---------|------------|----------------|------------|------------------------|-------------------------------|
| Claude Code | Installed tools | environment-specific | medium | Confidence rationale: source files prove declared tool surfaces, while actual installed availability is inherited from the parent Claude Code session (`speckit-pro/agents/codebase-analyst.md:12-20`; `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:30-38`). | Absent disposition: documented fallback path; TACD-002 should direct Claude agents to choose by needed capability and report missing MCPs as built-in fallback use with lower confidence. |
| Claude Code | MCP/app connectors | environment-specific | medium | Confidence rationale: plugin agents can list MCP tools, but plugin agents cannot declare their own MCP server connections, so parent session configuration decides availability (`speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:13-15`, `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:30-38`). | Absent disposition: downstream owner decision needed; TACD-003 should keep a non-blocking advisory and TACD-004 should test behavior without assuming a fixed connector list. |
| Claude Code | Skills/plugins | source-backed | high | Confidence rationale: the Claude plugin manifest identifies `speckit-pro` as the plugin package and the repo has concrete skill and agent roots under `speckit-pro/` (`speckit-pro/.claude-plugin/plugin.json:1-20`). | Absent disposition: downstream owner decision needed; TACD-002 can use a shared reference only if active Claude agent/skill entrypoints point to it or carry an approved equivalent. |
| Claude Code | Repo-local helpers | source-backed | high | Confidence rationale: active agent guidance names local fallback tools such as `Read`, `Glob`, and `Grep`, including the fallback chain in `speckit-pro/agents/codebase-analyst.md:57-69`. | Absent disposition: documented fallback path; local file tools remain valid fallback when no installed context tool exists, with confidence and local file references in output. |
| Codex | Installed tools | environment-specific | medium | Confidence rationale: Codex TOML agents encode capability instructions in `developer_instructions`, but callable tools depend on the active Codex session and installed connectors (`speckit-pro/codex-agents/codebase-analyst.toml:35-52`). | Absent disposition: downstream owner decision needed; TACD-002 should use capability names and Codex tool-discovery surfaces instead of hardcoded vendor-first wording. |
| Codex | MCP/app connectors | environment-specific | medium | Confidence rationale: Codex dependency metadata names MCP dependencies for the autopilot skill sidecar, while runtime availability still depends on installed connectors (`speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16`). | Absent disposition: downstream owner decision needed; exact dependency IDs should remain metadata until TACD-002 proves a generic declaration path or approved equivalent. |
| Codex | Skills/plugins | source-backed | high | Confidence rationale: the Codex plugin manifest points skills to `./codex-skills/` and describes bundled Codex custom-agent templates (`speckit-pro/.codex-plugin/plugin.json:22-43`). | Absent disposition: downstream owner decision needed; a shared reference is valid only if Codex skill entrypoints and installed custom-agent templates point to it or carry an approved equivalent. |
| Codex | Repo-local helpers | source-backed | high | Confidence rationale: Codex agent instructions explicitly include fallbacks to search/read files when RepoPrompt-like tools are unavailable (`speckit-pro/codex-agents/codebase-analyst.toml:40-52`). | Absent disposition: documented fallback path; Codex can continue with local search/read/shell helpers and lower confidence where evidence quality drops. |

## Probe Appendix

These probes were run locally and recorded as sanitized summaries.

| Probe | Command Summary | Result | Interpretation |
|-------|-----------------|--------|----------------|
| Branch/worktree | `git rev-parse --abbrev-ref HEAD` | `tacd-001-platform-mechanics-spike` | Correct feature branch. |
| Agent surfaces | `find speckit-pro/agents speckit-pro/codex-agents -maxdepth 1 -type f | sort | wc -l` | 21 files | Audit spans both Claude and Codex agent source roots. |
| Generated payload surfaces | `find dist/claude/speckit-pro dist/codex/speckit-pro -maxdepth 3 -type f | sort | wc -l` | 54 files | Generated duplicates exist and should not be edited directly in this spike. |
| Named optional-tool matches | `rg -l "Tavily|tavily|Context7|context7|RepoPrompt|repoprompt|MCP|mcp" speckit-pro tests/speckit-pro docs -S \| wc -l` | 59 files | TACD-004 should use category-aware enforcement rather than a blind ban. |
| Capability-language matches | `rg -l "capability|capabilities|installed tool|app connector|MCP|mcp" speckit-pro tests/speckit-pro docs -S \| wc -l` | 84 files | Existing repo already has capability vocabulary, but it is not a final directive contract. |
| Prerequisite check | `check-prerequisites.sh docs/ai/specs/.process/TACD-001-workflow.md` | all checks pass; MCP advisory reported missing optional named MCP set with fallbacks | Confirms the current prerequisite report is non-blocking but still names specific MCPs. |
| Scope review before report edit | `git diff --name-only` | empty | Phase 7 started from a clean checkpoint after confidence gate. |

The prerequisite probe output is intentionally summarized; this report does not commit raw runtime inventories or connector lists beyond the script's fixed advisory category.

## Directive-Home Recommendation

Recommend a shared capability-discovery reference plus runtime-specific pointers and approved equivalents.

Why this is preferable:

- The PRD and design concept want one product behavior: agents discover by capability and preserve formerly named tools only when they are actually the best available installed option. Evidence: `docs/prd-tool-agnostic-capability-discovery.md:24-28` and `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:219-224`.
- Claude and Codex surfaces differ: Claude plugin agents use Markdown frontmatter and inherit parent MCP configuration; Codex uses TOML agents, plugin skill metadata, and installed custom-agent templates. Evidence: `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:13-15`, `speckit-pro/.codex-plugin/plugin.json:22-43`, and `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16`.
- A shared source of truth reduces semantic drift, but each runtime needs a pointer or approved equivalent that fits its loading model.

Proof bar for TACD-002/TACD-004:

- Static pointer coverage must prove every active Claude agent, active Codex agent, relevant skill entrypoint/reference, and future eval expectation either points to the shared directive or carries an approved runtime-specific equivalent.
- Pointer target resolution must prove the referenced directive exists from the installed runtime context.
- Functional eval scenarios must prove behavior, not just text: agents should explain installed-capability discovery, select fallback capabilities when named MCPs are unavailable, cite source/capability paths, and report lower confidence when fallback quality is lower.
- Exact runtime/dependency metadata IDs may stay only where the platform schema or dependency declaration requires them, or until TACD-002 proves an equivalent generic declaration.

Fallback if static pointer coverage or eval-plan coverage cannot be proven: use runtime-specific directive copies, with a shared source-of-truth note and TACD-004 drift checks.

## TACD-004 Allowlist Recommendation

| Category | Allowed Status | Description | Example Evidence | False-Positive Guard |
|----------|----------------|-------------|------------------|----------------------|
| active runtime guidance | blocked after TACD-002 | Agent instructions that prefer or require named optional tools for behavior. | `speckit-pro/agents/domain-researcher.md:53-67`, `speckit-pro/codex-agents/domain-researcher.toml:33-49` | Do not block exact IDs in schema/dependency metadata until equivalent behavior is proven. |
| runtime/dependency metadata | review | Exact IDs required by a runtime, dependency schema, or installer metadata. | `speckit-pro/codex-skills/speckit-autopilot/agents/openai.yaml:9-16` | Review for whether it is metadata or user-facing guidance. |
| prerequisite/user-facing messaging | blocked after TACD-003 | Setup checks and docs that present a fixed optional MCP set. | `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh:115-142` | Preserve non-blocking health signal, but make categories generic. |
| deterministic/eval expectation | blocked after TACD-004 | Tests or evals that assert vendor-specific optional-tool wording. | `tests/speckit-pro/layer3-functional/evals/speckit-autopilot-evals.json:107-116` | Update after active behavior changes, not before. |
| generated source-derived duplicate | allowed if source-derived | Generated payload copies of active source content. | `dist/claude/speckit-pro/agents/codebase-analyst.md:52-67` | Do not hand-edit generated payloads. Regenerate from changed source. |
| historical/provenance | allowed | PRD, roadmap, changelog, archive, or fixture text documenting past decisions. | `docs/ai/specs/tool-agnostic-capability-discovery-design-concept.md:20-27` | Require clear archival/planning context. |
| fixture/test-only | review | Test fixture content that may intentionally contain named examples. | `tests/speckit-pro/layer4-scripts/fixtures/**` | Enforce only when fixture represents active expected behavior. |
| ambiguous/requires-review | review | Reference cannot be confidently classified. | N/A | Must name candidate categories, missing evidence, confidence, and owner. |
| out-of-scope | allowed | Unrelated project names or examples not part of SpecKit Pro capability guidance. | Trigger fixtures mentioning unrelated MCP project names | Avoid broad string bans on generic `mcp` vocabulary. |

## Downstream Handoff

### TACD-002: Agent Guidance

Inputs:

- this report's audit inventory and platform mechanics matrix
- `speckit-pro/agents/*.md`
- `speckit-pro/codex-agents/*.toml`
- relevant `speckit-pro/skills/speckit-autopilot/references/**` and Codex skill references
- generated payload regeneration path

Non-goals:

- prerequisite messaging and public docs wording, except where an agent reference points to them
- final eval enforcement

Validation needed:

- static pointer coverage for Claude and Codex active guidance
- generated payload regeneration or proof that generated files are source-derived and refreshed
- functional eval plan for capability selection and fallback confidence

### TACD-003: Prerequisite And Documentation Messaging

Inputs:

- prerequisite script evidence from `speckit-pro/skills/speckit-autopilot/scripts/check-prerequisites.sh:115-142`
- plugin limitation docs evidence from `speckit-pro/skills/speckit-autopilot/references/plugin-limitations.md:66-86`
- Codex prerequisite wording from `speckit-pro/codex-skills/speckit-autopilot/references/prerequisites-codex.md:109-114`

Non-goals:

- changing active agent decision logic
- changing final test/eval expectations before TACD-004

Validation needed:

- generic non-blocking advisory
- no claim that any named MCP is required
- clear fallback quality language

### TACD-004: Enforcement And Evals

Inputs:

- allowlist categories above
- Layer 3 eval evidence in both Claude and Codex eval files
- Layer 5 tool-scoping evidence in `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.sh:240-250`
- directive-home proof bar from this report

Non-goals:

- inventing the runtime directive before TACD-002
- deleting historical/provenance mentions

Validation needed:

- deterministic check for active named-tool prose outside approved categories
- static pointer coverage and target resolution for shared directive or approved equivalents
- functional evals for installed-capability discovery, fallback behavior, evidence path, citations/local files, and confidence reporting

## Verification Evidence

- Report path exists: `docs/ai/research/tool-agnostic-capability-discovery-spike.md`.
- Report is scoped to TACD-001 and does not edit active runtime guidance, prerequisite behavior, docs messaging, generated payload semantics, or enforcement tests.
- Source citations are repo-relative and point to local evidence.
- Appendix probes are summarized and sanitized.
- TACD-002/TACD-003/TACD-004 handoffs are explicit.

Reviewer order:

1. Read Summary and Directive-Home Recommendation.
2. Review Audit Inventory classifications.
3. Review Platform Mechanics Matrix for Claude and Codex.
4. Review TACD-004 Allowlist Recommendation.
5. Confirm downstream handoffs match the roadmap.

Known gaps:

- This spike does not prove live Claude Code or Codex runtime invocation behavior with full installed connector matrices.
- This spike does not rewrite active guidance, so current named optional-tool references intentionally remain.
- This spike does not run final AI evals; TACD-004 owns behavior-observable eval updates.

Rollback or flags:

- Roll back by reverting this report and TACD-001 process artifacts only.
- No runtime flag is needed because this slice changes no shipped behavior.

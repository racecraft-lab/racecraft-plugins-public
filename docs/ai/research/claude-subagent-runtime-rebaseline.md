# Claude Code Subagent Runtime Rebaseline

**Status:** Current source baseline
**Retrieved:** 2026-08-30
**Authority:** Current official Anthropic documentation, resolved through
Context7 as `/websites/code_claude`

## Scope

This record surveys every Claude Code subagent shipped by the active
`speckit-pro` plugin. It excludes the two repository-development helpers under
root `.claude/agents/`; those are not marketplace payload agents.

The current source roster contains 14 shipped agents:

| Cohort | Agents |
|---|---|
| Quality-critical | `phase-executor`, `implement-executor`, `analyze-executor` |
| Structured work | `checklist-executor`, `artifact-author`, `uat-runbook-author` |
| Read-only reasoning | `clarify-executor`, `codebase-analyst`, `spec-context-analyst`, `domain-researcher` |
| Orchestration support | `consensus-synthesizer`, `gate-validator` |
| Untrusted feedback | `sweep-classifier`, `sweep-analyst` |

`autopilot-fast-helper` remains an optional contract-only future role, not a
shipped Claude agent. The successor machine-readable roster is
`tests/speckit-pro/layer6-efficiency/fixtures/claude-agent-roster-rebaseline-v2.json`.

## Persistent memory decision

Claude supports `memory: user`, `project`, and `local`. With automatic memory
enabled, the agent receives memory instructions and up to the first 200 lines
or 25 KB of `MEMORY.md`.

| Agent group | Decision | Rationale |
|---|---|---|
| `implement-executor` | Adopt `memory: local` | Verified repository locations, conventions, and recurring gotchas can help later tasks without committing runtime notes |
| `codebase-analyst`, `spec-context-analyst` | Adopt `memory: local` | Claude Code 2.1.251 UAT proved confined memory-only writes, marker exclusion, and useful fresh-session recall |
| Phase/checklist/analyze/clarify executors | None | Current workflow artifacts are authoritative |
| `domain-researcher` | None | External facts drift |
| Synthesizer/gate/artifact/UAT roles | None | Deterministic current inputs should decide each result |
| Sweep roles | Never | Reviewer/model text is attacker-influenced and must not persist |

Current inputs always override memory. Never persist secrets, personal data,
raw reviewer/external text, current diffs, task state, unresolved hypotheses,
or unverified commands. The complete contract is
`speckit-pro/skills/speckit-autopilot/references/subagent-memory-policy.md`.

Existing project-scope memory is not moved or deleted. New local memory lives
under ignored `.claude/agent-memory-local/`.

## Frontmatter capability disposition

| Capability | Disposition |
|---|---|
| `name`, `description`, `model`, `effort`, `maxTurns` | Already used; structurally validated across the exact roster |
| `tools` | Used only as a narrow allowlist for the two untrusted sweep roles |
| `disallowedTools` | Retained for role boundaries; retired team-management names removed |
| `memory` | Adopted as `local` only for `implement-executor`, `codebase-analyst`, and `spec-context-analyst` after exact-client UAT |
| `background` | Retained for read-only analysts where current dispatch expects it |
| `skills` | Not preloaded; current prompts and capability discovery are authoritative |
| `isolation` | Not added to agents; removed from Phase 7 parallel dispatch because isolated branches do not guarantee the parent feature HEAD |
| `hooks`, `mcpServers`, `permissionMode` | Not adopted; plugin-shipped agents ignore them |
| `initialPrompt` | Not adopted; not part of the documented plugin-agent subset |
| experimental cache TTL | Client capability recorded at 2.1.248+, but not adopted for plugin agents |

## Versioned runtime policy

Runner helper `resolve-claude-subagent-runtime` turns bounded observations into
one replayable record and persists it in workflow evidence.

| Client baseline | Policy |
|---|---|
| 2.1.178+ | Named `Agent` team semantics are eligible only with env, interactive-mode, and live-contract gates |
| 2.1.217+ | Default concurrent subagent limit 20; older compatibility default 5 |
| 2.1.219+ | Default nesting depth 3; SpecKit workflow dispatch remains flat |
| 2.1.246+ | One partial result may continue by the same agent ID |
| 2.1.247+ | Native model fallback availability is recorded as operator-controlled, never plugin-owned |
| 2.1.248+ | Client cache TTL availability is recorded, not adopted in plugin frontmatter |

Every concurrency limit reserves one slot for recovery, producing
`wave_size = max(1, limit - 1)`. Invalid overrides warn and force wave size 1.
Results are accumulated in task order, independent of completion order.

On clients with partial-result support, the orchestrator sends one continuation
to the returned agent ID. A second partial result stops. Older clients receive
one fresh retry and then stop.

## Agent Teams correction

Agent Teams are an optional coordination path, not the correctness path.

- Teams require the environment flag, Claude Code 2.1.178+, positively
  interactive execution, and exact-client UAT of the required contract.
- `claude -p` always uses ordinary subagents.
- Named `Agent` calls may become teammates; ordinary subagent calls omit
  `name`.
- Current teammate documentation does not establish application of every
  subagent field. A use site that depends on `disallowedTools`, `memory`,
  `maxTurns`, `skills`, or per-agent effort stays on ordinary subagents unless
  the exact boundary is proven.
- Current Claude Code owns team creation and cleanup. Speckit Pro uses named
  Agent semantics and graceful shutdown, not removed legacy management tools.

## Parallel mutation correction

Phase 7 now parallelizes only tasks with explicit, disjoint file ownership in
the shared current checkout. Overlap and unknown ownership serialize. Per-agent
worktree isolation is omitted because a worktree subagent can start from the
repository default branch instead of the parent feature HEAD. Typecheck and unit
tests run after each bounded wave; regression recovery is serial.

## CAR successor boundary

The frozen CAR-003 v1 corpus remains immutable evidence for its historical
11-shipped-agent-plus-helper design. It is not silently rewritten.

The v2 current-source roster binds all 14 shipped agents plus the optional
contract-only helper, adds `artifact-author` to structured work, and adds both
sweep roles to an untrusted-feedback cohort with an immutable-broker-only hard
gate. CAR-006 consumes the v2 roster. Native fallback remains an operator
override; an unqualified delivered model is ineligible for a release claim.

## Live UAT gate

Before publication on a new Claude client family:

1. Run a two-session `implement-executor` memory cycle in a disposable Git
   repository. Verify only durable knowledge persists and no secret/ephemeral
   marker appears.
2. Probe both analysts for useful curation and repository-mutation denial.
   Add `memory: local` only if both confinement and value pass.
3. Force a low-turn partial result and verify one same-agent continuation.
4. Set concurrency to 2 and verify the resolver emits deterministic one-worker
   waves plus the reserved recovery slot. Probe the client's two-worker cap
   separately from the workflow policy.
5. Verify interactive named-Agent teammate semantics and that `-p` uses the
   ordinary-subagent fallback.
6. Run disjoint parallel edits from a feature commit and confirm current feature
   state is retained; verify overlapping ownership is serialized.

Do not manufacture account overload or availability failures. Cover those paths
with deterministic resolver fixtures.

### 2026-08-30 result — Claude Code 2.1.251

The maintained disposable-repository UAT passed:

- `implement-executor`, `codebase-analyst`, and `spec-context-analyst` wrote
  only ignored local-memory state, excluded the task-only marker, and recalled
  useful durable context in a fresh session.
- A one-turn `partial-worker` returned partial; the parent continued agent
  `a9fc302fa6bc1e8c1` exactly once and recovered both required markers.
- With `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS=2`, the resolver reserved one slot
  (`wave_size=1`). A separate direct client probe started exactly two disjoint
  workers, retained `codex/feature-uat`, and created no worktree.
- Two workers claiming the same output ran as foreground calls in strict
  completion order, proving the overlapping-ownership path stayed serial.
- Headless `-p` calls reported ordinary subagents. In an interactive session
  with the team flag enabled, an explicit named `Agent` call created teammate
  `verifier`; its marker arrived through the team mailbox, graceful shutdown
  was approved, the teammate was removed, and Claude cleaned the team directory.
  The maintained prompt must describe the named `Agent` contract directly and
  must not ask the model to discover retired `TeamCreate` tooling.

No overload, account failure, or provider outage was manufactured. Those
branches remain deterministic resolver-fixture coverage.

## Official sources

- <https://code.claude.com/docs/en/sub-agents>
- <https://code.claude.com/docs/en/agent-teams>
- <https://code.claude.com/docs/en/plugins-reference#agents>
- <https://code.claude.com/docs/en/worktrees>

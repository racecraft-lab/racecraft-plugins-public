---
topic: "Durable Claude and Codex parity for speckit-pro agents and skills"
slug: "single-source-host-parity"
date: "2026-09-29"
mode: "standalone"
source_input:
  type: "topic"
  ref: "2026-09 coherence audit seam review and the official Codex custom-agent and skills documentation"
question_count: 9
stop_reason: "natural"
---

# Design Concept: Durable Claude and Codex parity for speckit-pro agents and skills

> **Source:** 2026-09 coherence audit seam review, and the official Codex custom-agent and skills documentation
> **Date:** 2026-09-29
> **Questions asked:** 9
> **Stop reason:** natural

## Problem

Claude enforces agent and skill contracts in structure: frontmatter tool
allowlists, broker-only MCP agents, and shared references read at run time.
Codex restates the same contracts as prose, in hand-kept TOML
`developer_instructions` and in `*-codex.md` skill overlays. So every behavior
change must land twice, and the copies drift. The audit found drift in:

- the Post closeout list size (11, 13 and 14 rows);
- the grounding G1 and G3 rules;
- the formal-author broker rule;
- the hardener placement;
- status worktree discovery;
- scaffold behavior;
- grill-me boundaries;
- the consensus-synthesizer contract.

The parity validators prove that twin files and pointer tokens exist, but never
that their content matches.

## Goals

- **One authored source per agent.** Each role's Claude agent `.md` body is its
  only authored source. The build generates each paired Codex TOML's
  `developer_instructions` from that body (Q1).
- **Generated TOMLs stay in place.** They are committed at
  `speckit-pro/codex-agents/*.toml`, marked generated in `.gitattributes`, and
  rebuilt by `scripts/refresh-release-artifacts.py`. Installers, validators and
  tests that read that path keep working (Q2).
- **Host markers.** Host-specific text is written inline as
  `<!-- host:codex -->` ... `<!-- /host -->` and `<!-- host:claude -->` ...
  `<!-- /host -->` blocks. The generator keeps the target host's blocks and
  strips the other's. The shipped Claude payload never carries Codex blocks
  (Q3).
- **Pairing manifest.** `agent_inventory.json` lists each role's hosts. Paired
  roles are generated. Single-host roles stay hand-authored on their own host:
  `autopilot-fast-helper` on Codex; `artifact-preview-observer`,
  `sweep-analyst` and `sweep-classifier` on Claude. A twin that the manifest
  does not list fails the check (Q4).
- **Limits derived from one allowlist.** Codex agent limits are derived from
  the Claude frontmatter, not restated by hand (Q5). The slice-1 probe decided
  where each one can be enforced:
  - no Write, Edit or MultiEdit tools gives `sandbox_mode = "read-only"`. This
    key is **advisory**: a spawned agent keeps the parent's sandbox. It is
    emitted to document intent, and the inventory's `codex.sandbox` is checked
    against it, but no check or doc may call it enforced;
  - each `mcp__plugin_speckit-pro_<server>__<tool>` gives a per-server broker
    allowlist. No agent-file `enabled_tools` form works, so none is emitted;
  - a project-level `PreToolUse` hook keyed on the payload's `agent_type`
    enforces the rest: it denies `apply_patch` for read-only roles and every
    MCP tool outside a role's broker allowlist;
  - a read-only role's shell writes stay a prose rule, because a hook cannot
    tell a shell write from a shell read.
- **Skill overlays use the same markers.** Each `speckit-pro/codex-skills/**`
  overlay merges back into its shared file as host blocks. The payload build
  emits per-host copies, so `dist/codex` gets only Codex text and `dist/claude`
  only Claude text (Q6).
- **Runner behavior settles conflicts.** Where a Claude file and its Codex twin
  disagree, the runner registry, helpers and tests are the truth:
  - an unexplained divergence becomes one shared text that matches them;
  - a divergence caused by a real host capability (tool names, team dispatch,
    sandbox) becomes a host block with a one-line reason (Q7).
- **Prove enforcement live.** Before any migration, a live Codex probe tests
  whether a generated read-only agent is refused a write, and is refused a
  broker tool outside its allowlist. The redacted evidence is committed. If a
  key is ignored, that limit falls back to prose or to a hook, and the gap is
  recorded (Q8). Result (slice 1, `codex-cli 0.156.0`): agent-file keys
  enforce neither limit; a project `PreToolUse` hook enforces both per role,
  except shell writes (evidence:
  `tests/speckit-pro/fixtures/codex-enforcement-probe/evidence.md`).
- **Slicing** (Q9): one gh-stack of vertical slices, each passing CI alone.
  1. The live Codex enforcement probe and the generator skeleton, with marker
     parsing and the pairing manifest.
  2. Generated agents and derived enforcement for all paired roles, plus the
     generated-versus-source drift check.
  3. One slice per skill family, merging its overlay into host markers.
     `speckit-autopilot` is split by reference file across 3 or 4 slices.
  4. The content-parity validator replaces the existence-only parity checks.

## Non-goals

- **No new neutral source format.** Claude `.md` stays the authoring format
  (Q1).
- **No change to single-host agents' authoring** (Q4).
- **No reliance on `model_instructions_file`.** It replaces Codex's built-in
  instructions and is not a per-agent include (Codex config reference).
- **No change to how either host loads skills.** Both keep the open Agent
  Skills layout (Codex skills documentation).

## Module and Interface Deltas

- **Agent generator (new):** a Python standard-library module run by
  `scripts/refresh-release-artifacts.py`. It reads the Claude `.md`,
  frontmatter and inventory, and writes the Codex TOML (Q1, Q2, Q5). It also
  derives each role's `PreToolUse` hook policy; a later slice ships the hook
  that applies it.
- **Bare `tools:` (decision):** in Claude a bare `tools:` line is YAML null
  and inherits every tool. The generator reads it as an empty allowlist and
  fails closed, so an agent that means "inherit" must omit the key.
- **`speckit-pro/agents/*.md` (changed):** gains host blocks where Codex text
  differs (Q3).
- **`speckit-pro/codex-agents/*.toml` (changed):** generated for paired roles,
  and stays hand-authored for `autopilot-fast-helper` (Q2, Q4).
- **`speckit_pro_runner/agent_inventory.json` (changed):**
  - it is the pairing manifest;
  - `codex.sandbox` is verified against the derived value (Q4, Q5).
- **`speckit_pro_runner/gates/payloads.py` (changed):**
  - it applies host-marker filtering when building each host's payload;
  - the `codex-skills` overlay copy is replaced by per-host emission (Q6).
- **`speckit-pro/codex-skills/**` (removed over the slices):** the content
  moves into shared files with host blocks (Q6).
- **Parity validators (changed):** `validate-skill-contracts.py`,
  `validate-agent-contracts.py` and the layer-5 tool-scoping validator compare
  generated output with source instead of file existence (Q9).
- **Grey box:** the exact marker grammar, the generator's module layout, and
  how the autopilot references split across slices belong to the
  implementer.

## Terms

| Term | Meaning in this spec | Differs from codebase usage? | Source |
| ---- | -------------------- | ---------------------------- | ------ |
| Host block | A marked region of shared text that ships only to one host | Yes: new | Q3 |
| Paired role | A role that ships on both hosts, with its Codex file generated | Yes: new | Q4 |
| Overlay | Today, a Codex copy of a skill file under `codex-skills/`; retired by this design | Yes: the concept is removed | Q6 |
| Derived enforcement | Codex `sandbox_mode` and `enabled_tools` computed from the Claude allowlist | Yes: new | Q5 |

## Verification Gates

- **Generated-artifact drift:** `python3 scripts/refresh-release-artifacts.py --check`
  fails on any hand edit to a generated TOML or host payload (Q2; evidence:
  the AGENTS.md Commands table).
- **Pairing and markers:**
  - layer-1 checks fail on an unlisted twin, an unbalanced or nested host
    block, a Codex block in the Claude payload, or a Claude block in the Codex
    payload;
  - unit tests cover the marker parser and the derived-enforcement mapping
    (Q3 to Q5).
- **Content parity:** for every paired role and merged skill file, the
  generated host text equals the source with the other host's blocks removed
  (Q9).
- **Live Codex probe:** done in slice 1. Agent-file `sandbox_mode` and
  `enabled_tools` are not enforced; a project `PreToolUse` hook keyed on
  `agent_type` denies `apply_patch` and out-of-allowlist MCP calls for one
  role while the parent is unaffected. The redacted evidence is committed
  (Q8).
- **Existing gates:** `run-all.py`, the CI default suite, ruff, mypy,
  `reference:check`, and `ripwire --quality-delta` with 0 regressions (evidence:
  AGENTS.md).
- **Formal methods: none.** This is a deterministic text transform with
  byte-level checks; a model adds cost without new assurance.

## Design Tree (Q&A log)

### Q1. What should be the single source for each agent's instructions?
**Branch:** interface
**Recommended answer:** Claude .md body
> 12 of the 13 Codex agents mirror a Claude `.md`, and Claude reads `.md` natively. This is the least churn.

**Alternatives offered:** a neutral source file; the Codex TOML as source.
**User's answer:** Claude .md body

### Q2. Where should the generated Codex agent TOMLs live?
**Branch:** data
**Recommended answer:** commit them in `codex-agents/`
> Installers, validators and tests read that path, and `artifact-consistency` catches drift.

**Alternatives offered:** generate into `dist` only.
**User's answer:** commit them in `codex-agents/`

### Q3. How should host-specific instruction text be expressed?
**Branch:** behavior and rules
**Recommended answer:** inline host markers
> Body similarity today is 69% to 94%, with the synthesizer at 39%. Differences stay next to the text they modify.

**Alternatives offered:** a per-agent delta file; no deltas allowed.
**User's answer:** inline host markers

### Q4. How should single-host agents be handled?
**Branch:** scope
**Recommended answer:** a pairing manifest
> `agent_inventory.json` already records each role's hosts.

**Alternatives offered:** author everything from Claude `.md` with a hosts flag.
**User's answer:** a pairing manifest

### Q5. Where should Codex agent limits come from?
**Branch:** security
**Recommended answer:** derive them from the Claude tools
> Codex custom agents accept any `config.toml` key, including `sandbox_mode` and `mcp_servers.<id>.enabled_tools` (Codex docs). One allowlist covers both hosts.

**Alternatives offered:** declare them in the inventory.
**User's answer:** derive them from the Claude tools
**Outcome (slice-1 probe):** the derivation stands, but the premise did not
hold. Codex accepts `sandbox_mode` in an agent file and then applies the
parent's sandbox, and no `enabled_tools` form limits a plugin broker. The
derived limits are enforced by a project `PreToolUse` hook keyed on
`agent_type`; `sandbox_mode` stays as an advisory key; shell writes by
read-only roles stay prose.

### Q6. How should Codex skill overlays become host deltas?
**Branch:** interface
**Recommended answer:** the same markers as agents
> The overlays hold 33 files, including a 3,095-line `phase-execution-codex.md`. One mechanism covers everything, and shared text exists once.

**Alternatives offered:** keep the overlay files and trim them.
**User's answer:** the same markers as agents

### Q7. When twins disagree, which text wins?
**Branch:** behavior and rules
**Recommended answer:** runner behavior wins
> This follows AGENTS.md "one source per contract".

**Alternatives offered:** Claude text wins.
**User's answer:** runner behavior wins

### Q8. How should structural enforcement be proven?
**Branch:** verification
**Recommended answer:** a live Codex probe
> The docs do not show plugin MCP servers restricted from an agent file. This repo has already met ignored plugin-agent keys on Claude (`permissionMode`, `hooks`).

**Alternatives offered:** unit tests only.
**User's answer:** a live Codex probe
**Outcome (slice 1):** the probe showed both agent-file limits are ignored,
which unit tests alone would have missed. It then showed a project hook can
deny one role's `apply_patch` and MCP calls while the parent's calls pass.
Evidence: `tests/speckit-pro/fixtures/codex-enforcement-probe/evidence.md`.

### Q9. How should the work be sliced?
**Branch:** slice sizing
**Recommended answer:** the probe, then agents, then skills
> `estimate-spec-size` for 4 stories, 90 files and 12 FRs returned `warn`: 3,880 estimated LOC and 10 suggested slices.

**Alternatives offered:** agents only now.
**User's answer:** the probe, then agents, then skills

## Open Questions

- **Resolved in slice 1:** neither form works inside a custom agent file.
  `mcp_servers.<server>.enabled_tools` without a transport makes Codex reject
  the agent file, and `plugins.<plugin>.mcp_servers.<server>.enabled_tools`
  is accepted and ignored. Broker allowlists are enforced by a project
  `PreToolUse` hook instead.
- **What:** whether the hook payload's `agent_type` field stays available.
  **Why deferred:** the Codex hooks guide documents `agent_type` only for
  `SubagentStart`; `PreToolUse` carries it in practice (observed in 0.156.0).
  **Suggested next step:** the slice that ships the hook reruns
  `run-hook-probe.py` against the current Codex release before it merges.

## Recommended Next Step

File this as the design issue, then implement slice 1 (the probe and the
generator skeleton) at once, as a gh-stack.

# Claude Agent Route Candidate Baseline and Role Contracts

**Research date (access date): 2026-07-14** | **Spec: CAR-001** | **Branch: `car-001-candidate-route-baseline`**

This is the human-readable research record for CAR-001. Its machine counterpart is
the JSON manifest `docs/ai/research/claude-agent-route-candidate-manifest.json`
(authored in a later unit). The record is the single source of evidence and
rationale; the manifest is the single source of machine data. They cross-reference
by `agent_name` and `agent_contract_id` and never duplicate data that can drift.

> **Authoring status.** This record is assembled across five implementation units.
> Unit 1 (this pass, tasks T001-T009) authored the comparator pin, the stdlib
> hashing method, the agent inventory, the Codex-helper source inventory, the
> route-policy surface sweep, the Layer 6 fixture-gap, the twelve hash triples, and
> the reviewability checkpoint. Sections marked with an authoring placeholder are
> filled by later units and must not be treated as complete yet.

> **Evidence basis for the inventory sections below.** Every value in the
> *Immutable production comparator*, *Agent inventory*, *Codex helper source
> inventory*, *Route-policy surface inventory*, *Layer 6 fixture gap*, and
> *Agent-file hash triples* sections is a direct observation read from the pinned
> comparator tag or the tracked repository tree — repository evidence, not a claim
> about Anthropic platform behavior. Platform facts (model-ID resolution, alias
> bindings, effort semantics) belong to the *Primary-source fact table* and carry
> URL + access date + verbatim quote; the four-class statement labeling is applied
> across the whole record in a later unit (task T013). Recording `model: opus` here
> means only "the shipped frontmatter contains the alias `opus`", never a claim
> about what that alias resolves to.

---

## Immutable production comparator

All agent bytes hashed and inventoried in this record are read from a single pinned
release identity, never the working tree, so the recorded identity is reproducible
forever from the tag.

| Field | Value |
|-------|-------|
| `release_tag` | `speckit-pro-v2.19.1` |
| `commit_sha` | `e343aa2e4ebcb2d48c501f285d7072cfd55722da` |
| Object type | `commit` (verified via `git cat-file -t`) |
| `pin_rationale` | Latest published release at research time; the consumer-installable identity, reproducible from the tag. Per-agent content hashes make later frontmatter drift detectable at agent granularity. |

**2.19.0 -> 2.19.1 reconciliation (task T002).** The design concept and scaffold-time
spec named `speckit-pro-v2.19.0` as a 2026-07-13 snapshot; `speckit-pro-v2.19.1` is
a real patch published later, descending from 2.19.0. The scoped diff

```
git diff speckit-pro-v2.19.0 speckit-pro-v2.19.1 -- speckit-pro/agents speckit-pro/codex-agents
```

is **empty** (verified: no output, no `--stat` rows). The agent `.md` files and the
Codex `.toml` files are byte-identical between the two tags, so every route tuple,
instruction hash, and full-file hash recorded here is unchanged by the refresh.
Pinning to 2.19.1 is a zero-data-impact refresh.

---

## Stdlib hashing method (task T003)

Python 3.11+ standard library only (`hashlib`, `subprocess` with an argv list and
`shell=False`, and `tomllib` for the Codex helper). No new Bash, no third-party
import. The transient helper that computes these hashes lives outside the repository
(session scratchpad) and is never committed under `speckit-pro/`, `tests/`, or
`dist/`.

**Byte source.** For any agent file, the exact bytes are read from the pinned tag:

```
git show speckit-pro-v2.19.1:<repo-relative-path>
```

captured as raw bytes (no text-mode newline translation, no working-tree filters).

**`instruction_sha256` (frontmatter-stripped body).** The frontmatter is the leading
YAML block delimited by the first pair of `---` fence lines (the opening `---` line
and its closing `---` line). The instruction body is **everything after the closing
`---` fence line**, hashed verbatim — byte-for-byte, no normalization of whitespace,
line endings, or content. The leading blank line that follows the closing fence is
retained (each agent body begins `\n# <Title>...`). `instruction_sha256 =
sha256(body_bytes)`. Because routes (`model`/`effort`) live in frontmatter, a pure
frontmatter route change leaves this hash unchanged (SC-007, verified by
recomputation in a later unit, task T027).

**`full_file_sha256` (whole file).** `sha256` over the complete file bytes including
the frontmatter block, for drift detection.

**Method validation.** The stripping logic was proven on `phase-executor` and
independently cross-checked by a second implementation (naive split on the first
`\n---\n` boundary) for `phase-executor`, `gate-validator`, and `uat-runbook-author`;
both implementations produce identical `instruction_sha256` values. Re-running the
computation twice produced byte-identical output (reproducible).

**Codex-helper provisional instruction hash — exact method so a later unit can
reproduce and finalize it.** `autopilot-fast-helper` has no Claude `.md` at the tag;
its contract-equivalent translated body does not exist yet (authored in unit 3). The
**provisional** `instruction_sha256` recorded here is computed over the Codex source
contract content as follows, and is flagged **provisional-pending-unit-3**:

1. Read the toml bytes: `git show speckit-pro-v2.19.1:speckit-pro/codex-agents/autopilot-fast-helper.toml`.
2. Parse with stdlib `tomllib.loads(<toml-text>)` and take the string value of the
   `developer_instructions` key (TOML multi-line basic string; the parser applies the
   standard trim of the newline immediately following the opening `"""`).
3. Encode that string as UTF-8 and `sha256` it. The `developer_instructions` value is
   **2645 bytes** UTF-8 at this tag; its `sha256` is the provisional
   `instruction_sha256` in the hash-triples table.

Unit 3 finalizes the helper's `instruction_sha256` by recomputing it over the
Claude-flavored contract-equivalent translated body it authors, replacing this
provisional value. `full_file_sha256` for the helper is already final: `sha256` over
the entire source toml (2938 bytes) with `hash_source: codex-toml-translation`.

---

## Agent inventory (task T004)

Eleven current Claude agents at the pinned tag. The route tuple is `model` + `effort`
from the agent-file YAML frontmatter; the role-prose source is the agent `.md` at the
tag (repo-relative; no absolute paths).

| Agent | `model` | `effort` | Role-prose source (`speckit-pro-v2.19.1:`) |
|-------|---------|----------|--------------------------------------------|
| analyze-executor | opus | max | `speckit-pro/agents/analyze-executor.md` |
| checklist-executor | opus | max | `speckit-pro/agents/checklist-executor.md` |
| clarify-executor | opus | max | `speckit-pro/agents/clarify-executor.md` |
| codebase-analyst | sonnet | max | `speckit-pro/agents/codebase-analyst.md` |
| consensus-synthesizer | sonnet | max | `speckit-pro/agents/consensus-synthesizer.md` |
| domain-researcher | sonnet | max | `speckit-pro/agents/domain-researcher.md` |
| gate-validator | sonnet | max | `speckit-pro/agents/gate-validator.md` |
| implement-executor | opus | max | `speckit-pro/agents/implement-executor.md` |
| phase-executor | opus | max | `speckit-pro/agents/phase-executor.md` |
| spec-context-analyst | sonnet | max | `speckit-pro/agents/spec-context-analyst.md` |
| uat-runbook-author | sonnet | max | `speckit-pro/agents/uat-runbook-author.md` |

Model split: `opus` for the five executor/remediation roles (analyze, checklist,
clarify, implement, phase); `sonnet` for the six analyst/validator/author roles
(codebase, consensus, domain, gate, spec-context, uat). All eleven ship `effort: max`.

**Other observed frontmatter subagent-config fields (repo evidence, for the later
`required_capabilities.subagent_fields` mapping).** These are additional frontmatter
keys present at the tag; the eight-tool denylist is `Write, Edit, MultiEdit,
NotebookEdit, Skill, Agent, TeamCreate, SendMessage`.

| Agent | `maxTurns` | `disallowedTools` | other |
|-------|-----------|-------------------|-------|
| analyze-executor | 100 | (none — inherits operator surface) | color: orange |
| checklist-executor | 100 | (none) | color: yellow |
| clarify-executor | 35 | the eight-tool denylist | color: pink |
| codebase-analyst | 50 | the eight-tool denylist | `background: true` |
| consensus-synthesizer | 15 | the eight-tool denylist | color: purple |
| domain-researcher | 50 | the eight-tool denylist | `background: true` |
| gate-validator | 10 | the eight-tool denylist | color: cyan |
| implement-executor | 100 | `Skill` | `memory: project` |
| phase-executor | 100 | (none) | color: cyan |
| spec-context-analyst | 50 | the eight-tool denylist | `background: true` |
| uat-runbook-author | 30 | `Skill, Agent, TeamCreate, SendMessage` | color: cyan |

---

## Codex helper source inventory (task T005)

Every field in `speckit-pro-v2.19.1:speckit-pro/codex-agents/autopilot-fast-helper.toml`,
enumerated so unit 3's `platform_field_mapping` table can be source-complete (no source
field silently dropped). This is the net-new twelfth agent; it has no Claude production
route (recorded absence).

**Top-level TOML keys**

| Field | Value at tag |
|-------|--------------|
| `name` | `"autopilot-fast-helper"` |
| `description` | `"Optional leaf helper for the SpecKit autopilot. Uses gpt-5.3-codex-spark for near-instant text-only compression, triage, and query drafting. Advisory only."` |
| `model` | `"gpt-5.3-codex-spark"` |
| `sandbox_mode` | `"read-only"` |
| `developer_instructions` | multi-line basic string (2645 bytes UTF-8); contract content enumerated below |

**`developer_instructions` contract content** (the role prose, four bounded jobs, hard
rules, and output formats that unit 3 translates contract-equivalently):

- **Role prose** — "# Autopilot Fast Helper": a *latency-first text helper* for the
  top-level autopilot orchestrator; does one small advisory text task quickly then
  returns control. "## Your Role": not an executor, reviewer, or decision-maker; a
  small text-only helper that reduces prompt size and speeds orchestration.
- **The four bounded jobs** ("## Your Allowed Jobs" — exactly one per invocation):
  1. **Compress** a long executor/workflow summary into a short parent-friendly brief.
  2. **Triage** an unresolved item into `codebase`, `spec-context`, `domain-research`,
     or `mixed`.
  3. **Draft search queries** for follow-up research by a stronger agent or the parent.
  4. **Normalize prompt context** into a compact evidence block for a later agent prompt.
- **Hard rules** (`<hard_constraints>` "## Rules"):
  1. **Advisory text only** — never claim to have fixed, validated, or resolved the issue.
  2. **Do not make final decisions** — no gate outcome, no consensus winner, no
     approve/reject of an artifact edit, no substituting for a real executor/analyst.
  3. **Do not mutate anything** — never edit files, propose patches, run commands, or
     act like it owns the task.
  4. **Do not spawn agents or ask for more work** — a leaf worker: return one result, stop.
  5. **Use only the context in the prompt** — no tool output, web search, or filesystem
     exploration; if context is insufficient, say so briefly and return the smallest
     useful fallback.
  6. **Prefer compact output** — short, structured, paste-ready; speed is the reason it exists.
- **Output formats** ("## Output Formats", one per job): **Compression** (`## Fast Brief`
  — Core issue / Relevant evidence / Suggested next agent), **Triage** (`## Fast Triage`
  — Primary bucket / Why / Escalate?), **Query Drafting** (`## Query Drafts` — bullet
  list), **Prompt Normalization** (`## Compact Context` — Question / Evidence block /
  Open uncertainty).

Mapping-hypothesis note (recorded, probe-gated, for unit 3): `sandbox_mode: read-only`
-> the shared read-only tool denylist posture; `model: gpt-5.3-codex-spark` -> a fast
Claude route (starting hypothesis `haiku` + explicit low effort), labeled and gated on
a capability question. Claude-only subagent fields with no Codex source (e.g.
`maxTurns`) are deferred to CAR-010 as proposed policy.

---

## Route-policy surface inventory (task T006, AC-1.1)

Every tracked, active surface that **encodes** or **consumes** agent route policy —
where "route policy" means the per-agent `model`/`effort` tuple, the tool-scoping
denylist, the cross-platform agent set, and agent-type dispatch selection. Every path
was verified to exist at `HEAD`/the tag; paths are repo-relative globs.

**Scope note.** The model/effort/tool-scoping tuples are *encoded* in exactly one
authored place — the Claude agent `.md` frontmatter (source) — and mirrored verbatim
into the generated `dist/**` payload and the installed-cache fixture. The Codex
`.toml` files encode the parallel Codex route (`model`/`sandbox_mode`). Everything
else in the table *consumes* route policy (validates it, benchmarks it, or dispatches
by agent-type). The autopilot skill and Layer 7 fixtures were verified **not** to
hardcode any model alias or effort (a repo-wide search for `opus|sonnet|haiku|
reasoning-effort` under `speckit-pro/skills/**` returned nothing) — they route by
agent-type name only.

### A. Source — encodes route policy

| Surface | Encodes |
|---------|---------|
| `speckit-pro/agents/*.md` (11) | Claude agent frontmatter: `model`, `effort`, `disallowedTools`, `maxTurns`, `background`, `memory`. **Primary encode surface.** |
| `speckit-pro/codex-agents/*.toml` (10, incl. `autopilot-fast-helper.toml`) | Codex agent config: `model`, `sandbox_mode` (and per-agent `approval_policy`). Codex-side route. |

### B. Generated payload mirrors — encode (mirror; regenerated from source)

| Surface | Mirrors |
|---------|---------|
| `dist/claude/speckit-pro/agents/*.md` (11) | Generated Claude payload copy of the agent frontmatter. |
| `dist/codex/speckit-pro/codex-agents/*.toml` (10) | Generated Codex payload copy of the Codex agent config. |

### C. Installed-cache mirror and proof

| Surface | Role |
|---------|------|
| `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/installed-cache/claude/speckit-pro/agents/*.md` (11) | Installed-cache fixture mirror of the Claude agents. |
| `docs/ai/specs/.process/XPLAT-009-installed-cache-proof.json` | Installed-cache tree-hash proof binding the `dist/claude/speckit-pro` payload to the installed-cache fixture (certifies the mirrored agent payload). |
| `tests/speckit-pro/unit/fixtures/plugin-bash-confinement/contracts/installed-cache-proof.schema.json` + `installed-cache-proof*.json` | Proof schema and proof-shape fixtures (Layer 4). |

### D. Structural validation — consumes / validates route policy

| Surface | Consumes |
|---------|----------|
| `tests/speckit-pro/layer1-structural/validate-agents.py` | Reads and validates Claude agent frontmatter (`model`, etc.). |
| `tests/speckit-pro/layer1-structural/validate-codex-agents.py` | Validates Codex `.toml` agent config. |
| `tests/speckit-pro/layer1-structural/validate-codex-parity.py` | **Encodes the cross-platform agent set** (`CC_ONLY_AGENTS = {gate-validator, consensus-synthesizer}`, `CODEX_ONLY_AGENTS = {autopilot-fast-helper}`) and enforces Claude<->Codex agent parity. |
| `tests/speckit-pro/layer1-structural/validate-payload-conformance.py` | Asserts `agents/` and `codex-agents/` exist and are non-empty in the payloads. |
| `tests/speckit-pro/layer1-structural/validate-payload-completeness.py` | Source -> `dist/**` payload completeness. |
| `tests/speckit-pro/layer1-structural/validate-plugin-payload.py` | Guards the plugin payload boundary (no `tests/`/`specs/` under the plugin dir). |

### E. Tool-scoping validation — consumes route policy

| Surface | Consumes |
|---------|----------|
| `tests/speckit-pro/layer5-tool-scoping/validate-tool-scoping.py` | Reads each agent's `disallowedTools` denylist and asserts no `tools:` allowlist / no vendor-qualified MCP tool pinning. |

### F. Efficiency evaluation — consumes route policy

| Surface | Consumes |
|---------|----------|
| `tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py` | Drives `claude -p --model <model>` and `-c model_reasoning_effort=<effort>` per agent; `SWEEP_CONFIGS` enumerates model configurations for cost-quality benchmarking. |
| `tests/speckit-pro/layer6-efficiency/fixtures/` (`consensus-synthesizer`, `gate-validator`) | Current Claude Layer 6 fixtures (see the fixture-gap section). |
| `tests/speckit-pro/layer6-efficiency/fixtures-codex/` (`codebase-analyst`, `domain-researcher`, `spec-context-analyst`) | Codex-side Layer 6 fixtures. |
| `tests/speckit-pro/layer6-efficiency/lib/quality-scorer.py`, `lib/token-counter.py`, `results-codex/consolidated-smoke-2026-05-25.json` | Harness support and historical smoke results. |

### G. Agent-type dispatch consumers (select agent by name; do not encode model/effort)

| Surface | Consumes |
|---------|----------|
| `speckit-pro/skills/speckit-autopilot/SKILL.md` and `references/{agent-teams-integration,consensus-protocol,gate-validation,phase-execution,plugin-limitations,post-implementation,prerequisites}.md` | Dispatch agents by type-name during the autopilot workflow (agent identity only; verified to carry no model/effort literal). |
| `speckit-pro/skills/grill-me/SKILL.md` | References agent names (human-in-the-loop; not autopilot dispatch). |
| `tests/speckit-pro/layer7-integration/dispatch-fixtures/**` | Multi-agent dispatch-graph fixtures: which agent-type the orchestrator dispatches per phase (dispatch routing, not model/effort). |
| Generated mirrors of the above under `dist/claude/**` and `dist/codex/**` | Payload copies of the dispatching skill references. |

### H. Meta-registration and governing documentation

| Surface | Role |
|---------|------|
| `tests/speckit-pro/suite-manifest.json` | Registers Layer 5 (tool scoping) and Layer 6 (efficiency) as evaluation layers — governs which route-policy validators run. |
| `docs/ai/specs/claude-agent-routing-technical-roadmap.md` (+ `-MOC.md`) | The master routing plan governing CAR-001..011 (governing documentation, not a runtime encode/consume surface). |

---

## Layer 6 Claude fixture gap (task T007)

Verified by listing `tests/speckit-pro/layer6-efficiency/fixtures/` (both the working
tree and the pinned tag). Of the twelve agents, **2 have a current Claude Layer 6
fixture and 10 do not**.

- **Current (2):** `consensus-synthesizer`, `gate-validator`.
- **Missing (10):** `analyze-executor`, `checklist-executor`, `clarify-executor`,
  `codebase-analyst`, `domain-researcher`, `implement-executor`, `phase-executor`,
  `spec-context-analyst`, `uat-runbook-author`, `autopilot-fast-helper`.

Note: a separate `fixtures-codex/` set covers three Codex-side agents
(`codebase-analyst`, `domain-researcher`, `spec-context-analyst`); it does not change
the Claude fixture gap above. This gap feeds the requirements-level fixture backlog
and Layer 6 labeling authored in a later unit.

---

## Agent-file hash triples (task T008)

All twelve `{instruction_sha256, full_file_sha256, hash_source}` triples, computed from
the pinned-tag bytes with the method above (Python 3.11 stdlib), reproduced identically
across two runs. A later unit copies these verbatim into the manifest
`agent_file_hashes`.

| Agent | `instruction_sha256` | `full_file_sha256` | `hash_source` |
|-------|----------------------|--------------------|---------------|
| analyze-executor | `6230b2e8dc80ecdebdef64da461e465ce9129073f1fa9359821023aedc2bf35d` | `e3ae8f36aa0cf1ad3343c6d68d8118d71781632e85871338cbdf846eb5c0c535` | claude-agent-md |
| checklist-executor | `8f6f512b76825cffe7078da685e6c728b48eb5e673d5c83913ca1e438e58e6e3` | `7c0129ca4a6e106f1f42a8b51c321b813db5340bed45644f822a96274274c2ea` | claude-agent-md |
| clarify-executor | `89ceb775b4ce0b98b516466ba30ee6fda147b6524690ee1fcfa024ddff0b8cc3` | `e18d74f13d312ad9547188728db57fb720468aae15b3b8ac7f478f0971fbafbe` | claude-agent-md |
| codebase-analyst | `c22addc989966637c7ecae0320f1692eda6168fd70ae2fa186deda927c8ffc8f` | `1cde5a8820173271d55d3077282caf9a4ad76bc92d90966e55b9fc70c587bac3` | claude-agent-md |
| consensus-synthesizer | `c4ac8820002ba3f24ca5192384a1f76f126183f147c4f3b23b00b4e12235a52c` | `548b9eeb69b6c3f8b8f5429a9ae567d456e4a4ddd1482efe1c1e947e84737327` | claude-agent-md |
| domain-researcher | `b831b9929674fe3b6dbc3d33559622219157dc4d319bf3c3b0bdae4a131c010c` | `be7237202cdc187443a2c246eaef72e9f566a496162b227ee9e4ff41b8481896` | claude-agent-md |
| gate-validator | `abba902b8e48ee4ba1ed3cf82c0350ebf11ba3586f6295c1881f841b5465b87e` | `ecfa70143aa02c943474f23d38cd5c0b01ca1fabae7d2a899c45d35eb7bb5f0d` | claude-agent-md |
| implement-executor | `91e0dbf81cb5f0adec0056af0f21e38426cd8f3684e40fd9e0a1cf2cdd1c2548` | `e5ae7f409d4c487e06790afa6b2b8609407a3a31f9dd8fc0358e21b72893d921` | claude-agent-md |
| phase-executor | `695d78c4dd80ee1c2a2f724dc62b1f67b55c710efbe12cc8ff7535af6a415a48` | `70bf046540039a16bf2fe1109d782c52f27c070ffaebc4c7a99f34347930179c` | claude-agent-md |
| spec-context-analyst | `faf387eabec1866ca87119023b04950ceda6949e7963eb8ba99aaad1eb43fd48` | `6659fb1b08ecfbdb784ab7f47d7c5ac9f8ce45b705de9cfea5144ac573edbc4f` | claude-agent-md |
| uat-runbook-author | `51a1b54a079eaf2325160dbfc5fd28548fcda6da3e88f62e800a60376f09c3e8` | `d4aeecbcc2fb486aac68bf0084460ff9c4c75cc5bb1ff74f9d2f728e6c9eb4ba` | claude-agent-md |
| autopilot-fast-helper | `0da3103f276542e615f2257f90514d58e3af9a61e6c59555d9c611ea7aff2b95` *(PROVISIONAL — pending unit 3)* | `aa570f8ff51fa3cb7848d8c05253ddf5d080f5d4a2dbed9a55f0149fceb1296d` | codex-toml-translation |

The helper's `instruction_sha256` is the provisional value over the 2645-byte
`developer_instructions` string (method documented above); unit 3 finalizes it over
the contract-equivalent translated body. Its `full_file_sha256` is over the 2938-byte
source toml and is final.

---

## Reviewability checkpoint (task T009)

Recorded before deliverable authoring: **0 production-code LOC, 2 deliverable files**
(`docs/ai/research/claude-agent-route-candidates.md` and
`docs/ai/research/claude-agent-route-candidate-manifest.json`), **1 primary surface**
(`docs/ai/research/`). All below the warn thresholds. Estimator advisory
`{estimated_loc: 0, suggested_slices: 1, status: ok}` (spike flag). **Result: within
budget; remains one spec, no split exception required.**

---

## Primary-source fact table

<!-- authored in unit 2 (Group A fact table, tasks T010-T014): model IDs, the four aliases, subagent config fields, effort levels, model-resolution precedence, plugin-agent field support, fast mode, authentication modes, non-interactive telemetry — each with URL + access date + verbatim quote and a four-class label -->

## Capability questions

<!-- authored in a later unit (Group D capability-question section, task T024; questions raised across T010/T013/T014) -->

## Fixture backlog

<!-- authored in a later unit (Group C requirements-level fixture backlog, task T021) — one entry per twelve agents; the Layer 6 fixture gap above is its input -->

## Telemetry requirements

<!-- authored in a later unit (Group C telemetry requirements, task T022) — non-interactive `claude -p --output-format json` fields per role, necessity-labeled -->

## Layer 6 labeling

<!-- authored in a later unit (Group C Layer 6 labeling, task T023) — label the current Layer 6 Claude path as bare prompt emulation; mark historical results non_release_evidence; state the CAR-003 lift condition -->

## Go / no-go handoff

<!-- authored in unit 5 (Group D handoff, task T025) — final section: enumerate the provisional manifest, role-contract catalog, fixture backlog, telemetry requirements, unresolved capability questions, and the go/no-go decision; assert no dependency on CAR-002 results and no executable claim before probing -->

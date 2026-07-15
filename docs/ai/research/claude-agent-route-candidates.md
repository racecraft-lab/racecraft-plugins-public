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

## Statement classification (task T013)

The record separates **four statement classes** with distinct visible tags. Official
Anthropic documentation is the *only* admissible source for any claim about Anthropic
platform behavior (FR-006).

| Tag | Class | Admissible source / meaning |
|-----|-------|-----------------------------|
| `[FACT]` | verified fact | Either a **platform fact** (official Anthropic docs — the only source for a platform-behavior claim; carries source URL + access date `2026-07-14` + short verbatim quote, per FR-004/SC-002) **or** a **repository fact** (a direct observation of the pinned comparator tag / tracked tree, reproducible from the tag). Platform-behavior claims may *only* be platform facts. |
| `[INFERENCE]` | reasonable inference | A conclusion composed from cited facts, not stated verbatim by any single source. Names its basis. |
| `[POLICY]` | proposed SpecKit Pro policy | A value or rule this project proposes (e.g. a Claude-only helper field), not an Anthropic-documented fact. Deferred to the named CAR spec. |
| `[ASSUMPTION]` | unverified assumption | A statement neither documented nor observed. The record contains none; any undocumented behavior is instead a capability question. |

**Record-wide class map.** Every declarative statement in the record falls into exactly
one `[FACT]`/`[INFERENCE]`/`[POLICY]`/`[ASSUMPTION]` class (SC-003). Capability questions
(`CAP-Qn`) are *open probes*, not declarative claims: they are the deliberate home for
unresolved / undocumented items (FR-005, FR-008) and carry none of the four labels.

| Record section | Dominant class | Notes |
|----------------|----------------|-------|
| Preamble, *Immutable production comparator*, *Stdlib hashing method*, *Agent inventory*, *Codex helper source inventory*, *Route-policy surface inventory*, *Layer 6 Claude fixture gap*, *Agent-file hash triples*, *Reviewability checkpoint* | `[FACT]` (repository facts) | Direct observations read from `speckit-pro-v2.19.1` / the tracked tree, reproducible from the tag — not platform-behavior claims. |
| *Codex helper source inventory* → the "Mapping-hypothesis note" | `[INFERENCE]` | `sandbox_mode: read-only` → shared read-only denylist; `gpt-5.3-codex-spark` → a fast Claude route (starting hypothesis `haiku` + explicit low effort) — probe-gated on CAP-Q3. |
| *Codex helper source inventory* → the `maxTurns` deferral clause | `[POLICY]` | Claude-only field with no Codex source; proposed value deferred to CAR-010. |
| *Primary-source fact table* | per-row tags | Each row carries its own `[FACT]`/`[INFERENCE]` tag inline. |
| *Capability questions* | unclassified (open probes) | `CAP-Q1…CAP-Q6`; the explicit home for unresolved bindings and undocumented behaviors. |

**No-overclaim assertions (FR-007).** No statement in this record claims a head-to-head
benchmark result between any two models, and none claims a native fallback or automatic
model-substitution feature beyond what the cited docs state. The only documented
substitution behavior — allowlist alias substitution for the **main-session** `/model`
and `--model` surfaces (row `RES-3`) — is recorded as a platform fact with its exact
quote. The **subagent-frontmatter** unavailable-model behavior and the execution-time
manifestation of alias re-pointing are recorded as capability questions (`CAP-Q5`,
`CAP-Q6`), never as facts.

**Conflict disposition (FR-005).** No unresolved conflict between two *current* official
claims was found among the recorded facts. Temporal supersessions (e.g. fast mode's
default moving from Opus 4.7 to Opus 4.8 across dated "what's new" entries — rows `FST-1`,
`FST-2`) are recorded as the current value plus the superseded prior value, not as
conflicts. Had a genuine conflict arisen, it would appear as a `CAP-Qn` with both claims
quoted verbatim and neither labeled a platform fact.

---

## Primary-source fact table

**Access date for every fact row below: 2026-07-14.** Every platform-fact row cites a
current official Anthropic page (`docs.claude.com`, `code.claude.com`, or `claude.com`),
carries a short verbatim quote, and bears exactly one class tag (FR-004, SC-002, SC-003).
Row IDs (e.g. `ALS-opus`, `RES-3`) are stable anchors the manifest and later units cite.
Inference rows name the facts they compose. Undocumented bindings/behaviors are not
recorded here — they live in *Capability questions* as `CAP-Qn`.

### 1. Model family and model IDs

- **`MDL-1`** — The current Claude model family and their Claude API IDs are: **Claude Fable 5** (`claude-fable-5`), **Claude Opus 4.8** (`claude-opus-4-8`), **Claude Sonnet 5** (`claude-sonnet-5`), and **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`, API alias `claude-haiku-4-5`). Only Haiku 4.5 carries a dated snapshot ID; the Opus/Sonnet/Fable API IDs equal their aliases. `[FACT]`
  - Source: https://docs.claude.com/en/docs/about-claude/models/overview (accessed 2026-07-14)
  - Quote: "Claude API ID | claude-fable-5 | claude-opus-4-8 | claude-sonnet-5 | claude-haiku-4-5-20251001" and "Claude API alias | claude-fable-5 | claude-opus-4-8 | claude-sonnet-5 | claude-haiku-4-5".
- **`MDL-2`** — Positioning: Opus 4.8 is the default recommendation for complex agentic coding; Fable 5 is the highest-capability option. `[FACT]`
  - Source: https://docs.claude.com/en/docs/about-claude/models/overview (accessed 2026-07-14)
  - Quote: "If you're unsure which model to use, start with Claude Opus 4.8 for complex agentic coding and enterprise work. For workloads that need the highest available capability, use Claude Fable 5."
- **`MDL-3`** — Modality of the current family (supports the manifest `required_capabilities.modality`): all current models take text and image input and produce text output. `[FACT]`
  - Source: https://docs.claude.com/en/docs/about-claude/models/overview (accessed 2026-07-14)
  - Quote: "All current Claude models support text and image input, text output, multilingual capabilities, and vision."

### 2. Claude Code model aliases and expected resolved IDs

The eleven current agents ship the Claude Code aliases `opus` and `sonnet` in frontmatter
(repository fact — *Agent inventory*); `haiku` and `fable` are candidate aliases. The
Claude Code aliases resolve to a *floating* target ("the latest X model" / "Claude Fable
5"), re-pointable by environment variables and provider allowlists — the docs never bind
an alias to a fixed dated ID. Therefore each alias's **documented behavior** is a
`[FACT]`, its **expected resolved ID** is an `[INFERENCE]` composed with `MDL-1`, and its
**environment-time binding** is a capability question (design Open Question 1; Edge Cases).
Per FR-012 / Q6, **no legacy dated model snapshot is enumerated as a separate candidate** —
candidates are the four aliases only, each with its expected resolved ID recorded alongside.

- **`ALS-opus`** — The `opus` alias uses the latest Opus model. `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "`opus` | Uses the latest Opus model for complex reasoning tasks".
  - Expected resolved model ID: `claude-opus-4-8` (Opus 4.8 is the current latest Opus, `MDL-1`). `[INFERENCE]` — composed from `ALS-opus` + `MDL-1`; the exact environment-time binding is **`CAP-Q1`**.
- **`ALS-sonnet`** — The `sonnet` alias uses the latest Sonnet model. `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "`sonnet` | Uses the latest Sonnet model for daily coding tasks".
  - Expected resolved model ID: `claude-sonnet-5` (Sonnet 5 is the current latest Sonnet, `MDL-1`). `[INFERENCE]` — binding probe **`CAP-Q2`**.
- **`ALS-haiku`** — The `haiku` alias uses the fast, efficient Haiku model. `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "`haiku` | Uses the fast and efficient Haiku model for simple tasks".
  - Expected resolved model ID: `claude-haiku-4-5-20251001` (API alias `claude-haiku-4-5`; the current Haiku, `MDL-1`). `[INFERENCE]` — binding probe **`CAP-Q3`**.
- **`ALS-fable`** — The `fable` alias uses Claude Fable 5. `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "`fable` | Uses Claude Fable 5 for your hardest and longest-running tasks".
  - Expected resolved model ID: `claude-fable-5` (`MDL-1`). `[INFERENCE]` — binding **and** environment-time availability (PRD OQ-4) probe **`CAP-Q4`**. `fable` stays an executor-class candidate regardless of announcement status (FR-013); excluded only by recorded probe/contract evidence.
- **`ALS-context`** — The alias namespace also documents `best` ("Uses Fable 5 where your organization has access to it, otherwise the latest Opus model") and `default` ("Special value that clears any model override and reverts to the recommended model for your account type, or to the organization default model when an admin has set one. Not itself a model alias"). These are **not** CAR candidate aliases (FR-012 fixes the candidate set to `opus`/`sonnet`/`haiku`/`fable`). `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: as embedded above.
- **`ALS-repoint`** — Alias resolution is re-pointable per family via environment variables, confirming the binding floats (basis for the invalidation triggers and `CAP-Q1…Q4`). `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "`ANTHROPIC_DEFAULT_OPUS_MODEL` | The model to use for `opus`, or for `opusplan` when Plan Mode is active." and "`ANTHROPIC_DEFAULT_FABLE_MODEL` | The model to use for `fable`, and the model ID Claude Code recognizes as Fable 5 for automatic model fallback on third-party providers".

### 3. Subagent configuration fields

- **`SUB-model`** — The subagent `model` frontmatter field accepts the four aliases, a full model ID, or `inherit` (default). `[FACT]`
  - Source: https://code.claude.com/docs/en/sub-agents (accessed 2026-07-14)
  - Quote: "Model to use: `sonnet`, `opus`, `haiku`, `fable`, a full model ID (for example, `claude-opus-4-8`), or `inherit`. Defaults to `inherit`".
- **`SUB-fields`** — The documented supported subagent frontmatter fields are: `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `mcpServers`, `hooks`, `maxTurns`, `skills`, `memory`, `effort`, `background`, `isolation`, `color`, `initialPrompt`. `[FACT]`
  - Source: https://code.claude.com/docs/en/sub-agents (accessed 2026-07-14)
  - Quotes (field descriptions, verbatim): `name` — "Unique identifier using lowercase letters and hyphens. Hooks receive this value as `agent_type`. The filename doesn't have to match"; `description` — "When Claude should delegate to this subagent"; `tools` — "Tools the subagent can use. Inherits all tools if omitted. To preload Skills into context, use the `skills` field rather than listing `Skill` here"; `disallowedTools` — "Tools to deny, removed from inherited or specified list"; `isolation` — "Set to `worktree` to run the subagent in a temporary git worktree… The worktree is automatically cleaned up if the subagent makes no changes"; `color` — "Display color for the subagent in the task list and transcript. Accepts `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, or `cyan`". (`maxTurns`, `memory`, `background`, `skills`, `mcpServers`, `hooks`, `permissionMode`, `initialPrompt` appear in the same supported-fields list; `effort` is row `EFF-1`.)
- **`SUB-permmodes`** — Documented `permissionMode` values. `[FACT]`
  - Source: https://code.claude.com/docs/en/sub-agents (accessed 2026-07-14)
  - Quote: "`default` | Standard permission checking with prompts"; "`acceptEdits` | Auto-accept file edits and common filesystem commands…"; "`auto` | Auto mode: a background classifier reviews commands and protected-directory writes"; "`dontAsk` | Auto-deny permission prompts (explicitly allowed tools still work)"; "`bypassPermissions` | Skip permission prompts"; "`plan` | Plan mode (read-only exploration)". (Note `SUB-permmodes` is honored only for non-plugin subagents — see `PLG-1`.)

### 4. Effort / reasoning levels

- **`EFF-1`** — The subagent `effort` field sets a per-agent effort level overriding the session level; documented levels are `low`, `medium`, `high`, `xhigh`, `max`, and available levels are model-dependent. `[FACT]`
  - Source: https://code.claude.com/docs/en/sub-agents (accessed 2026-07-14)
  - Quote: "Effort level when this subagent is active. Overrides the session effort level. Default: inherits from session. Options: `low`, `medium`, `high`, `xhigh`, `max`; available levels depend on the model".
- **`EFF-2`** — The `/effort` command takes a level or `auto`, and the interactive level set additionally includes `ultracode`. `[FACT]`
  - Source: https://code.claude.com/docs/en/commands (accessed 2026-07-14)
  - Quote: "`/effort [level|auto]`" with levels "`low` `medium` `high` `xhigh` `max` `ultracode`".
- **`EFF-3`** — Opus 4.8 defaults to high effort. `[FACT]`
  - Source: https://code.claude.com/docs/en/whats-new/2026-w22 (accessed 2026-07-14)
  - Quote: "It defaults to high effort; use `/effort xhigh` for harder tasks."
  - Note: all eleven current agents ship `effort: max` (repository fact, *Agent inventory*); `max` is the top documented frontmatter level (`EFF-1`), above Opus 4.8's `high` default. `[INFERENCE]` — composed from `EFF-1` + `EFF-3` + inventory.

### 5. Model-resolution precedence

- **`RES-1`** — For subagents, `CLAUDE_CODE_SUBAGENT_MODEL` overrides both the Agent-tool `model` parameter and the subagent's `model` frontmatter; `inherit` restores normal resolution. `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "The model to use for all subagents and agent teams. Overrides the per-invocation `model` parameter and the subagent definition's `model` frontmatter. Set to `inherit` to use normal model resolution instead".
- **`RES-2`** — The subagent-model surfaces (order of the resolution chain). `[FACT]`
  - Source: https://docs.claude.com/en/docs/claude-code/model-config (accessed 2026-07-14)
  - Quote: "Subagent models: the `model` field in subagent frontmatter, the Agent tool's `model` parameter, `CLAUDE_CODE_SUBAGENT_MODEL`, and, on v2.1.197 and earlier, the model picker in the `/agents` wizard".
- **`RES-3`** — Aliases resolve to the newest permitted family version; an allowlist can pin versions, and a substitution is announced — documented for the **main-session** `/model` and `--model` surfaces only. `[FACT]`
  - Source: https://docs.claude.com/en/docs/claude-code/model-config (accessed 2026-07-14)
  - Quote: "a model family alias, `opus`, `sonnet`, `haiku`, or `fable`, resolves to the newest version of its family that the allowlist permits. When the allowlist pins specific versions, for example `[\"sonnet\", \"claude-opus-4-6\"]`, both `/model opus` and `--model opus` select Claude Opus 4.6, the newest permitted Opus, and show a notice naming both the requested and substituted models."
- **`RES-4`** — Main-session model surfaces. `[FACT]`
  - Source: https://docs.claude.com/en/docs/claude-code/model-config (accessed 2026-07-14)
  - Quote: "Main session model: `/model`, the `--model` flag, the `ANTHROPIC_MODEL` environment variable, the `model` setting, and the model restored when resuming a session".
- **`RES-5`** — Selecting an unrecognized model id (via the `/model` custom-model surface) reports an error. This is documented for `/model`, **not** for subagent-frontmatter dispatch (see `CAP-Q5`). `[FACT]`
  - Source: https://code.claude.com/docs/en/model-config (accessed 2026-07-14)
  - Quote: "Model \"<name>\" is not a recognized model id."

### 6. Plugin-agent field support

The speckit-pro agents are **plugin-shipped** agents, so plugin-agent field support governs
which of their frontmatter fields the platform honors.

- **`PLG-1`** — Plugin agents honor a subset of subagent fields; `hooks`, `mcpServers`, and `permissionMode` are **not** supported for plugin-shipped agents. `[FACT]`
  - Source: https://code.claude.com/docs/en/plugins-reference (accessed 2026-07-14)
  - Quote: "Plugin agents support `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`, and `isolation` frontmatter fields. The only valid `isolation` value is `\"worktree\"`. For security reasons, `hooks`, `mcpServers`, and `permissionMode` are not supported for plugin-shipped agents."
- **`PLG-2`** — Plugin agents are addressed by a plugin-scoped name. `[FACT]`
  - Source: https://code.claude.com/docs/en/plugins-reference (accessed 2026-07-14); corroborated by https://code.claude.com/docs/en/hooks (accessed 2026-07-14)
  - Quote: "Agents appear in the @-mention typeahead under their scoped name, such as `my-plugin:code-reviewer`, once the plugin is enabled" and (hooks) "For subagents shipped by a plugin, this is the plugin-scoped identifier such as `my-plugin:reviewer`, not the bare frontmatter name."

### 7. Fast mode

- **`FST-1`** — Fast mode is a high-speed Opus configuration (same model quality, ~2.5x speed, higher per-token cost). `[FACT]`
  - Source: https://code.claude.com/docs/en/whats-new/2026-w20 (accessed 2026-07-14)
  - Quote: "Fast mode is a high-speed Opus configuration: the same model quality at about 2.5x the speed for a higher per-token cost, useful for rapid iteration and live debugging."
- **`FST-2`** — Fast mode currently defaults to Opus 4.8 (superseding the earlier Opus 4.7 default), priced at 2x standard for ~2.5x speed. `[FACT]`
  - Source: https://code.claude.com/docs/en/whats-new/2026-w22 (accessed 2026-07-14); https://claude.com/pricing (accessed 2026-07-14)
  - Quote: "Fast mode now defaults to Opus 4.8 at $10/$50 per MTok: 2x the standard rate for about 2.5x the speed." and (pricing) "Get up to 2.5x faster speeds with fast mode for Opus 4.8 at 2x standard pricing."
- **`FST-3`** — `/fast` toggles fast mode; in print mode (`-p`) it only works when the session was launched with `fastMode` in `--settings`. `[FACT]`
  - Source: https://code.claude.com/docs/en/commands (accessed 2026-07-14)
  - Quote: "Toggle fast mode on or off. In non-interactive mode (`-p`), `/fast` works only in a session launched with fast mode in its `--settings` value, for example `claude -p --settings '{\"fastMode\": true}'`… Requires Claude Code v2.1.205 or later".
  - Note: fast mode is a **session-level** Opus configuration and is absent from the supported subagent frontmatter fields (`SUB-fields`, `PLG-1`), so it is orthogonal to per-agent route policy — a subagent does not opt into fast mode via frontmatter. `[INFERENCE]` — composed from `FST-1` + `SUB-fields`/`PLG-1`.

### 8. Authentication modes

- **`AUTH-1`** — Claude Code authenticates individuals, teams, and organizations. `[FACT]`
  - Source: https://code.claude.com/docs/en/authentication (accessed 2026-07-14)
  - Quote: "Log in to Claude Code and configure authentication for individuals, teams, and organizations."
- **`AUTH-2`** — Documented authentication modes, in the page's precedence order: `CLAUDE_CODE_USE_BEDROCK` / `CLAUDE_CODE_USE_VERTEX` / `CLAUDE_CODE_USE_FOUNDRY` (cloud providers), `ANTHROPIC_AUTH_TOKEN` (sent as `Authorization: Bearer`), `ANTHROPIC_API_KEY` (sent as `X-Api-Key`), `apiKeyHelper`, `CLAUDE_CODE_OAUTH_TOKEN` (a long-lived token from `claude setup-token`), and interactive subscription login (`/login`). `[FACT]`
  - Source: https://code.claude.com/docs/en/authentication (accessed 2026-07-14)
  - Quote (the "Authentication precedence" identifiers, verbatim): "CLAUDE_CODE_USE_BEDROCK … CLAUDE_CODE_USE_VERTEX … CLAUDE_CODE_USE_FOUNDRY … ANTHROPIC_AUTH_TOKEN … Authorization: Bearer … ANTHROPIC_API_KEY … X-Api-Key … apiKeyHelper … CLAUDE_CODE_OAUTH_TOKEN … claude setup-token … /login".
  - Note: agents inherit the session's auth mode; no agent requires a specific mode. The manifest `required_capabilities.client` is therefore "Claude Code, any supported auth mode." `[INFERENCE]` — composed from `AUTH-2` + `RES-2`.

### 9. Non-interactive telemetry

**These rows are the source for the *Telemetry requirements* section (task T022, later unit).**

- **`TEL-1`** — `claude -p --output-format json` returns a structured payload with `result` (text), session id, usage metadata, `total_cost_usd`, and a per-model cost breakdown; `--json-schema` adds `structured_output`. `[FACT]`
  - Source: https://code.claude.com/docs/en/headless (accessed 2026-07-14)
  - Quote: "With `--output-format json`, the response payload includes `total_cost_usd` and a per-model cost breakdown…"; "`json`: structured JSON with result, session ID, and metadata"; "The response includes metadata about the request (session ID, usage, etc.) with the structured output in the `structured_output` field."
- **`TEL-2`** — No effort field is documented among the `-p --output-format json` result fields; the effective reasoning effort applied is therefore not returned by the print-mode JSON result. `[INFERENCE]` — composed from the documented `TEL-1` field set (result / session id / usage / `total_cost_usd` / per-model cost / `structured_output`), which contains no effort field. Feeds the T022 "never-returned / derived" necessity label.
- **`TEL-3`** — OpenTelemetry monitoring emits the `claude_code.cost.usage` metric whose attributes include `model`, `query_source` (`"main"`/`"subagent"`/`"auxiliary"`), `speed` (`"fast"`), `effort` (`"low"`/`"medium"`/`"high"`/`"xhigh"`/`"max"`), and `agent.name` — so per-subagent, per-model, per-effort cost is observable via OTel (a surface distinct from the `-p` JSON result). `[FACT]`
  - Source: https://code.claude.com/docs/en/monitoring-usage (accessed 2026-07-14)
  - Quote (verbatim metric + attribute identifiers): "`claude_code.cost.usage` … `model` … `query_source` `\"main\"` `\"subagent\"` `\"auxiliary\"` … `speed` `\"fast\"` … `effort` `\"low\"` `\"medium\"` `\"high\"` `\"xhigh\"` `\"max\"` … `agent.name`".
- **`TEL-4`** — The OTel `claude_code.api_request` log event carries `model`, `cost_usd`, `duration_ms`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_creation_tokens`, and `request_id`. `[FACT]`
  - Source: https://code.claude.com/docs/en/monitoring-usage (accessed 2026-07-14)
  - Quote (verbatim event + field identifiers): "`claude_code.api_request` … `model` … `cost_usd` … `duration_ms` … `input_tokens` … `output_tokens` … `cache_read_tokens` … `cache_creation_tokens` … `request_id`".
- **`TEL-5`** — The model a subagent actually runs on is observable as the `resolvedModel` field (SubagentStart hook), which can differ from the requested `model`. For background subagents the tool response carries `resolvedModel` but no usage fields. `[FACT]`
  - Source: https://code.claude.com/docs/en/hooks (accessed 2026-07-14)
  - Quote: "The `resolvedModel` field names the model the subagent actually runs on, which can differ from the `model` value in `tool_input`, such as when `availableModels` or another override applies. It requires Claude Code v2.1.174 or later." and "For background subagents, the tool returns immediately after launching, so `tool_response` carries no usage fields. It has `status: \"async_launched\"`, `agentId`, `description`, `prompt`, `outputFile`, and `resolvedModel`."

### 10. Pricing (cost context)

- **`PRC-1`** — Current published per-model list prices ($/MTok input / output): Fable 5 $10 / $50; Opus 4.8 $5 / $25; Sonnet 5 $2 / $10 (introductory) then $3 / $15; Haiku 4.5 $1 / $5. `[FACT]`
  - Source: https://claude.com/pricing (accessed 2026-07-14)
  - Quote: "Fable 5 … Input $10/ MTok … Output $50/ MTok"; "Opus 4.8 … Input $5/ MTok … Output $25/ MTok"; "Sonnet 5 … Input $2/ MTok … Output $10/ MTok"; "Haiku 4.5 … Input $1/ MTok … Output $5/ MTok".
- **`PRC-2`** — Sonnet 5 introductory pricing runs through 2026-08-31, then standard. `[FACT]`
  - Source: https://www.anthropic.com/news/claude-sonnet-5 (accessed 2026-07-14)
  - Quote: "Claude Sonnet 5 is available everywhere today at an introductory price of $2 per million input tokens and $10 per million output tokens through August 31, 2026. It then moves to standard pricing at $3 per million input tokens and $15 per million output tokens."

## Capability questions

Stable, contiguous probe IDs established by this unit (unit 2, tasks T010/T013/T014).
Later units reference these IDs verbatim: the manifest `capability_questions` stubs (T020)
and each tuple's `binding_question_ref` / `probe_question_ref` (T017) resolve here, and the
dedicated capability-question prose pass (T024) expands each entry below without renumbering.
Capability questions are **open probes**, not declarative statements — they carry none of
the four class tags (per FR-005/FR-008) and hand undocumented bindings and behaviors to
CAR-002 for probe design.

Sources of these questions: unbound alias→dated-ID bindings (T010, rows `ALS-opus…fable`);
inter-doc conflicts (T013 — **none found**, so no conflict-driven question); and the two
undocumented behaviors (T014). No candidate is claimed executable before these are probed.

| ID | Question (one-line) | Blocks |
|----|---------------------|--------|
| **`CAP-Q1`** | Does the `opus` Claude Code alias resolve to `claude-opus-4-8` in the pinned benchmark environment, and is that alias→dated-ID binding stable given "latest"-family resolution, allowlist pinning, and `ANTHROPIC_DEFAULT_OPUS_MODEL` re-pointing (`ALS-opus`, `RES-3`, `ALS-repoint`)? | CAR-002 probe of the `opus` route's environment-time resolved ID; gates candidate-tuple binding for the five `opus` executor agents (analyze/checklist/clarify/implement/phase). |
| **`CAP-Q2`** | Does the `sonnet` alias resolve to `claude-sonnet-5` in the pinned environment, and is that binding stable under the same floating-resolution/allowlist/re-point risks (`ALS-sonnet`)? | CAR-002 probe of the `sonnet` route's resolved ID; gates candidate-tuple binding for the six `sonnet` analyst/validator/author agents (codebase/consensus/domain/gate/spec-context/uat). |
| **`CAP-Q3`** | Does the `haiku` alias resolve to `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) in the pinned environment (`ALS-haiku`)? | CAR-002 probe of the `haiku` route's resolved ID; gates the `autopilot-fast-helper` starting-hypothesis `haiku` + low-effort candidate tuple (helper Mapping-hypothesis note). |
| **`CAP-Q4`** | Does the `fable` alias resolve to `claude-fable-5` **and** is `fable` available/accessible in the pinned benchmark environment (PRD OQ-4), given `best`/`fable` "where your organization has access" gating and `ANTHROPIC_DEFAULT_FABLE_MODEL` re-pointing (`ALS-fable`, `ALS-context`, `ALS-repoint`)? | CAR-002 probe of `fable`'s resolved ID and environment-time availability; gates `fable`'s executor-class candidate eligibility (FR-013) — `fable` is excluded only by recorded probe/contract evidence. |
| **`CAP-Q5`** | When a subagent's `model` frontmatter names an **unavailable** model at dispatch, does Claude Code hard-error or silently substitute another model? (Documented only for the main-session `/model` custom-model surface — `RES-5`, the `model_not_found` API-retry category — never for subagent-frontmatter dispatch.) | CAR-002 probe of unavailable-model dispatch behavior; gates any CAR-003 fallback design that assumes a defined unavailable-model outcome. Recorded as a mandatory probe question, never assumed (FR-008). |
| **`CAP-Q6`** | At a subagent's execution time, when a shipped alias has **re-pointed** to a new resolved model ID, is the new model silently used, does it hard-error, or is it otherwise handled? (Distinct from and additional to alias re-pointing's role as a recorded manifest invalidation trigger, FR-014; the docs surface the resolved model via `resolvedModel`/`TEL-5` and announce main-session substitution via `RES-3`, but do not document the subagent execution-time manifestation.) | CAR-002 probe of alias re-pointing's execution-time manifestation; gates CAR-003 route-stability assumptions and the semantics of the per-alias invalidation triggers. Recorded as a mandatory probe question, never assumed (FR-008). |

Each `CAP-Qn` above states the **detection/probe** need only; the *Go / no-go handoff*
(task T025, final section) carries any that remain unverified as no-go items or open
questions, and asserts no dependency on CAR-002 results.

### Capability-question prose (CAP-Q1…CAP-Q6)

Full prose for each capability question, consolidating the probes raised by the alias-binding
rows (`ALS-opus…ALS-fable`, task T010), the inter-doc conflict scan (task T013 — none found, so
no conflict-driven question), and the two undocumented behaviors (task T014). The IDs are stable
and match the manifest `capability_questions` stubs verbatim; this pass adds prose and does not
renumber. All six are **open probes**, not declarative claims — they carry none of the four class
tags (FR-005/FR-008), and no candidate is claimed executable before they are answered.

- **`CAP-Q1` — `opus` environment-time binding.** Does the `opus` Claude Code alias resolve to
  `claude-opus-4-8` in the pinned benchmark environment, and is that alias-to-dated-ID binding
  stable? The docs bind `opus` only to "the latest Opus model" (`ALS-opus`), and `claude-opus-4-8`
  is today's latest Opus (`MDL-1`) — but that is a recorded *inference*, not a settled binding: the
  target floats and is re-pointable via `ANTHROPIC_DEFAULT_OPUS_MODEL` and allowlist pinning
  (`ALS-repoint`, `RES-3`). CAR-002 must probe the environment-time resolved ID. **Blocks:** the
  `opus/max` candidate binding for the five `opus` executors (analyze/checklist/clarify/implement/
  phase) and the `opus` upshift candidate on the six `sonnet` analysts.
- **`CAP-Q2` — `sonnet` environment-time binding.** Does the `sonnet` alias resolve to
  `claude-sonnet-5` in the pinned environment, and is that binding stable under the same
  floating-resolution, allowlist-pinning, and re-pointing risks (`ALS-sonnet`, `RES-3`,
  `ALS-repoint`)? **Blocks:** the `sonnet` candidate tuples for the six `sonnet` analyst/validator/
  author agents (codebase/consensus/domain/gate/spec-context/uat), the `sonnet` lower-cost candidate
  on the five executors, and the helper's `sonnet` fallback.
- **`CAP-Q3` — `haiku` environment-time binding.** Does the `haiku` alias resolve to
  `claude-haiku-4-5-20251001` (API alias `claude-haiku-4-5`) in the pinned environment (`ALS-haiku`,
  `MDL-1`)? **Blocks:** the `autopilot-fast-helper` starting-hypothesis `haiku` + low-effort candidate
  binding, and the `haiku` candidate tuples on the six analyst roles.
- **`CAP-Q4` — `fable` binding and availability.** Does the `fable` alias resolve to `claude-fable-5`
  **and** is `fable` available/accessible in the pinned benchmark environment (PRD OQ-4), given the
  `best`/`fable` "where your organization has access" gating (`ALS-context`) and
  `ANTHROPIC_DEFAULT_FABLE_MODEL` re-pointing (`ALS-fable`, `ALS-repoint`)? **Blocks:** `fable`'s
  executor-class candidate eligibility and environment-time availability across the five executors.
  `fable` stays an executor-class candidate and is excluded only by recorded probe/contract evidence
  (FR-013), never by announcement status.
- **`CAP-Q5` — unavailable-model dispatch (undocumented).** When a subagent's `model` frontmatter
  names an **unavailable** model at dispatch, does Claude Code hard-error or silently substitute
  another model? The error path is documented only for the main-session `/model` custom-model surface
  (`RES-5`, the `model_not_found` category) — **never** for subagent-frontmatter dispatch. Recorded as
  a mandatory probe question, never assumed (FR-008). **Blocks:** any CAR-003 fallback design that
  assumes a defined unavailable-model dispatch outcome for the twelve agents.
- **`CAP-Q6` — alias re-pointing execution-time manifestation (undocumented).** At a subagent's
  execution time, when a shipped alias has **re-pointed** to a new resolved model ID, is the new model
  silently used, does it hard-error, or is it otherwise handled? This is distinct from and additional
  to alias re-pointing's role as a recorded manifest invalidation trigger (FR-014): the docs surface
  the resolved model via `resolvedModel`/`TEL-5` and announce main-session substitution via `RES-3`,
  but do not document the subagent execution-time manifestation. Recorded as a mandatory probe
  question, never assumed (FR-008). **Blocks:** CAR-003 route-stability assumptions and the semantics
  of the per-alias invalidation triggers recorded on every agent entry.

## Fixture backlog

Requirements-level backlog only — one entry per the twelve agents (FR-019, SC-004). Each entry
states the role contract to exercise (from the manifest `role_contract`), representative task types,
required evidence (tool surface, mutation boundary, output format), and a pass/fail signal sketch.
It contains **no full fixture specifications** — concrete inputs, golden outputs, and fixture wiring
are CAR-003's deliverable, not this spike's. Each subsection anchor matches that agent's manifest
`fixture_backlog_ref`. Two agents (`consensus-synthesizer`, `gate-validator`) already have a current
Claude Layer 6 fixture (see *Layer 6 Claude fixture gap*); their entries note what a CAR-003
role-contract fixture must add beyond that smoke fixture. The other ten have no current Claude fixture.

*Statement class: these entries are `[INFERENCE]`/`[POLICY]` — the "role contract to exercise" restates
repository facts (the shipped agent contract at the pinned tag), while the representative tasks, required
evidence, and pass/fail sketches are fixture requirements this project proposes for CAR-003. No new
platform fact and no benchmark result is asserted.*

### Fixture backlog: analyze-executor

- **Role contract to exercise** — runs `/speckit-analyze`, then researches and remediates every finding
  at all severities (CRITICAL/HIGH/MEDIUM/LOW), applying evidence-grounded fixes to the feature's
  spec/plan/tasks artifacts (production route `opus/max`).
- **Representative task types** — a spec/plan/tasks set seeded with findings across all four severities,
  including at least one cross-artifact inconsistency and one finding whose fix requires external evidence.
- **Required evidence** — *Tool surface:* full operator surface with **no** `disallowedTools` denylist;
  the fixture confirms the agent can invoke `Skill` (`/speckit-analyze`), `Read`/`Write`/`Edit`, and
  `Bash`. *Mutation boundary:* read-write confined to `spec.md`/`plan.md`/`tasks.md`; no cross-spec or
  shipped-payload writes. *Output format:* structured analysis-and-remediation summary (findings by
  severity, fixes applied, residual gaps).
- **Pass/fail signal sketch** — PASS when every seeded finding is surfaced at its correct severity and
  remediated with cited evidence, edits land only in the three artifacts, and the summary enumerates
  fixes and residual gaps. FAIL on a missed or misclassified finding, an evidence-free fix, a write
  outside the artifact boundary, or a malformed summary.

### Fixture backlog: checklist-executor

- **Role contract to exercise** — runs a single `/speckit-checklist` domain, then researches and
  remediates any `[Gap]` markers, applying evidence-grounded fixes to `spec.md` or `plan.md`
  (production route `opus/max`).
- **Representative task types** — a spec + plan seeded with one checklist domain containing several
  `[Gap]` markers, at least one requiring external best-practice evidence to close.
- **Required evidence** — *Tool surface:* full operator surface, no denylist; `Skill`
  (`/speckit-checklist`), `Read`/`Write`/`Edit`, `Bash`. *Mutation boundary:* read-write on
  `spec.md`/`plan.md` only. *Output format:* checklist-domain result (gaps found, evidence, fixes applied).
- **Pass/fail signal sketch** — PASS when each `[Gap]` is closed with cited evidence, edits stay confined
  to `spec.md`/`plan.md`, and the result lists gaps, evidence, and fixes. FAIL on an unremediated gap, an
  evidence-free fix, an out-of-boundary write, or a missing result structure.

### Fixture backlog: clarify-executor

- **Role contract to exercise** — prepares a single Clarify question set: inspects the workflow prompt,
  spec, and repo evidence and returns prioritized questions with recommended answers and evidence for the
  parent orchestrator to apply; never edits artifacts and never waits on a user (production route
  `opus/max`, read-only).
- **Representative task types** — an underspecified spec plus a workflow prompt that requires a
  prioritized set of clarifying questions with recommended answers.
- **Required evidence** — *Tool surface:* read-only — `Read`/`Grep`/`Glob` plus read-only `Bash`
  inspection; the eight-tool write/dispatch denylist (`Write, Edit, MultiEdit, NotebookEdit, Skill,
  Agent, TeamCreate, SendMessage`) is enforced (the fixture confirms a write/dispatch attempt is denied).
  *Mutation boundary:* strictly read-only — zero artifact edits, no dispatch, no wait-on-user. *Output
  format:* prioritized clarify question set, each item carrying a recommended answer and supporting evidence.
- **Pass/fail signal sketch** — PASS when the set is prioritized, each item has a recommended answer plus
  evidence, and the run makes no edits or dispatches and never blocks on user input. FAIL on any artifact
  mutation, any dispatch, a question lacking a recommended answer or evidence, or a wait-on-user hang.

### Fixture backlog: codebase-analyst

- **Role contract to exercise** — analyzes the existing codebase to resolve a question, gap, or finding
  from the perspective of established code patterns and conventions; returns a structured answer with
  file-level evidence; used in autopilot consensus rounds (production route `sonnet/max`, `background:true`,
  read-only).
- **Representative task types** — a consensus question about code patterns or conventions answerable only
  by reading the codebase.
- **Required evidence** — *Tool surface:* read-only — `Read`/`Grep`/`Glob` plus read-only `Bash`; the
  eight-tool denylist is enforced; `background:true`. *Mutation boundary:* read-only. *Output format:*
  structured answer with file-level codebase evidence (file references).
- **Pass/fail signal sketch** — PASS when the answer cites concrete file-level evidence, stays within the
  read-only tool surface, and returns in the consensus structure. FAIL on any mutation, an answer without
  file-level evidence, or the wrong output shape. Background note: per `TEL-5` a background subagent's
  async-launch response carries `resolvedModel` but no usage fields, so the fixture must capture cost/usage
  from the completed run (see *Telemetry requirements*).

### Fixture backlog: consensus-synthesizer

- **Role contract to exercise** — synthesizes the three consensus analysts' outputs into one actionable
  answer with a confidence assessment: applies the 2-of-3 agreement rule, flags all-disagree cases for
  human review, and produces exact artifact edits for the orchestrator to apply (does not apply them)
  (production route `sonnet/max`, read-only). Has a current Layer 6 fixture.
- **Representative task types** — one input set of three analyst outputs at 2-of-3 agreement, and a second
  set where all three disagree.
- **Required evidence** — *Tool surface:* read-only — `Read`/`Grep`/`Glob`; the eight-tool denylist is
  enforced. *Mutation boundary:* read-only — emits proposed edits as text; the orchestrator applies them.
  *Output format:* synthesized answer plus confidence assessment plus exact proposed artifact edits.
- **Pass/fail signal sketch** — PASS when 2-of-3 agreement yields the agreed answer with a confidence
  assessment, the all-disagree set is flagged for human review, and proposed edits are emitted as text
  (not applied). FAIL when the agent applies an edit itself, mis-resolves the agreement rule, or omits the
  confidence or the human-review flag. Beyond the current smoke fixture: a CAR-003 fixture must add the
  read-only tool-surface enforcement and real dispatch-context treatment that the bare-prompt Layer 6
  fixture omits (see *Layer 6 labeling*).

### Fixture backlog: domain-researcher

- **Role contract to exercise** — researches industry best practices and official documentation to resolve
  a question, gap, or finding with an evidence-based recommendation; used across Clarify, Checklist, and
  Analyze consensus phases (production route `sonnet/max`, `background:true`, read-only).
- **Representative task types** — a question that can be resolved only by external best-practice or
  official-documentation research.
- **Required evidence** — *Tool surface:* read-only research — `Read` plus `WebSearch` plus `WebFetch`;
  the eight-tool denylist is enforced; `background:true`. *Mutation boundary:* read-only. *Output format:*
  recommendation backed by external-documentation and community best-practice citations.
- **Pass/fail signal sketch** — PASS when the recommendation cites external sources and stays within the
  read-only research tool surface. FAIL on any mutation, an uncited recommendation, or missing
  `WebSearch`/`WebFetch` use where the task requires external evidence. Background telemetry note as for
  `codebase-analyst`.

### Fixture backlog: gate-validator

- **Role contract to exercise** — runs gate-validation commands (marker checks, metric thresholds) and
  returns pass/fail with structured JSON evidence; validates gates G0-G7 after each autopilot phase
  (production route `sonnet/max`, read-only). Has a current Layer 6 fixture.
- **Representative task types** — an artifact set constructed to pass some gates and fail others, spanning
  both marker-presence and metric-threshold checks.
- **Required evidence** — *Tool surface:* read-only — `Read` plus `Bash` (runs gate-validation commands)
  plus `Grep`; the eight-tool denylist is enforced. *Mutation boundary:* read-only — runs validation and
  reports results; no edits. *Output format:* pass/fail gate result with structured JSON evidence.
- **Pass/fail signal sketch** — PASS when each gate verdict matches ground truth and the JSON evidence is
  well-formed and parseable. FAIL on a wrong gate verdict, any mutation, or malformed JSON. Beyond the
  current smoke fixture: a CAR-003 fixture must add read-only tool-surface enforcement and structured-output
  proof (`structured_output` via `--json-schema`; see *Telemetry requirements*, *Layer 6 labeling*).

### Fixture backlog: implement-executor

- **Role contract to exercise** — executes a single implementation task using strict TDD
  red-green-refactor: writes a failing test first, verifies it FAILs, writes the minimum implementation to
  pass, then refactors; returns structured TDD evidence (production route `opus/max`; `memory: project`).
- **Representative task types** — one well-scoped implementation task with a clear, testable behavior.
- **Required evidence** — *Tool surface:* full operator surface **except** `Skill` (`disallowedTools:
  Skill`); the fixture confirms `Skill` is denied while `Read`/`Write`/`Edit`/`Bash` work. *Mutation
  boundary:* read-write on the task's test and implementation files (TDD). *Output format:* structured TDD
  evidence (failing test, FAIL verification, minimal implementation, refactor).
- **Pass/fail signal sketch** — PASS when the transcript shows red (a failing test plus an observed FAIL)
  before green (the minimal passing implementation) and then a refactor, edits stay confined to the test
  and implementation files, and `Skill` is unused/denied. FAIL on green-before-red (no observed failing
  test), any `Skill` invocation, or an out-of-scope write.

### Fixture backlog: phase-executor

- **Role contract to exercise** — executes a single SpecKit phase (Specify, Plan, or Tasks) by running the
  `/speckit-*` command via the `Skill` tool at high reasoning effort; returns a concise summary of files
  created, metrics, markers, and errors (production route `opus/max`).
- **Representative task types** — one invocation per phase — Specify, Plan, Tasks — each from a prepared
  upstream state.
- **Required evidence** — *Tool surface:* full operator surface, no denylist; `Skill`
  (`/speckit-specify`, `/speckit-plan`, `/speckit-tasks`), `Read`/`Write`/`Edit`, `Bash`. *Mutation
  boundary:* read-write producing the phase artifacts (`spec.md`/`plan.md`/`tasks.md`) via the
  Skill-invoked command; no cross-spec writes. *Output format:* concise phase-result summary (files
  created, metrics, markers found, errors).
- **Pass/fail signal sketch** — PASS when the Skill-invoked phase produces the expected artifact and the
  summary reports files, metrics, markers, and errors, with writes confined to the current spec. FAIL on a
  missing or misplaced artifact, a cross-spec write, or absent summary fields.

### Fixture backlog: spec-context-analyst

- **Role contract to exercise** — analyzes the project constitution, technical roadmap, and prior spec
  artifacts to resolve a question, gap, or finding from the perspective of established project decisions
  and principles; used across consensus phases (production route `sonnet/max`, `background:true`, read-only).
- **Representative task types** — a consensus question answerable only from project decisions and
  principles (constitution, roadmap, or prior specs).
- **Required evidence** — *Tool surface:* read-only — `Read`/`Grep`/`Glob`; the eight-tool denylist is
  enforced; `background:true`. *Mutation boundary:* read-only. *Output format:* answer grounded in project
  decisions and specifications.
- **Pass/fail signal sketch** — PASS when the answer cites project-decision sources and stays read-only.
  FAIL on any mutation, an answer ungrounded in project artifacts, or the wrong shape. Background telemetry
  note as for `codebase-analyst`.

### Fixture backlog: uat-runbook-author

- **Role contract to exercise** — rewrites a deterministic UAT runbook skeleton into a plain-English,
  executable acceptance runbook a non-engineer can follow: concrete numbered steps with observable expected
  results, plain setup prose, and a real FR-coverage mapping; edits the skeleton in place; fail-open
  (production route `sonnet/max`).
- **Representative task types** — a generated UAT skeleton (placeholder per-story checkboxes, a raw Env
  Setup table, a circular FR Coverage Matrix) to rewrite; plus a malformed or partial skeleton to exercise
  the fail-open path.
- **Required evidence** — *Tool surface:* `Read`/`Edit`/`Write`; `disallowedTools: Skill, Agent,
  TeamCreate, SendMessage` (the fixture confirms these are denied). *Mutation boundary:* read-write on the
  UAT runbook skeleton file **only**, edited in place; fail-open — on any trouble it leaves the skeleton
  untouched and never blocks PR creation. *Output format:* edited-in-place runbook (numbered steps with
  observable expected results, plain setup prose, a real FR-coverage matrix).
- **Pass/fail signal sketch** — PASS when the good skeleton becomes concrete numbered steps, plain setup
  prose, and a real FR mapping edited in place, and the malformed skeleton is left untouched (fail-open, no
  crash, no block). FAIL on a dispatch attempt, an edit outside the skeleton file, a hard failure that
  blocks PR creation, or placeholder content left unrewritten on the good input.

### Fixture backlog: autopilot-fast-helper

- **Role contract to exercise** — optional latency-first, text-only leaf helper for the top-level autopilot
  orchestrator: performs exactly one small advisory text task per invocation (compress, triage, draft
  search queries, or normalize prompt context), then returns control; advisory only, not an executor,
  reviewer, or decision-maker (no current Claude production route — recorded absence; candidate route
  `haiku` + low effort, `CAP-Q3`).
- **Representative task types** — one fixture per bounded job: (1) compress a long executor/workflow
  summary; (2) triage an unresolved item into `codebase`, `spec-context`, `domain-research`, or `mixed`;
  (3) draft search queries; (4) normalize prompt context; plus an insufficient-context input to exercise
  the "say so briefly and return the smallest useful fallback" rule.
- **Required evidence** — *Tool surface:* **no tools** — advisory text only; uses only prompt context (no
  `Write`/`Edit`, no `Skill`/`Agent`/dispatch, no web or filesystem); read-only denylist posture (Codex
  `sandbox_mode: read-only` maps to the shared read-only denylist per the helper's `platform_field_mapping`).
  *Mutation boundary:* strictly read-only and non-mutating — never edits files, proposes patches, runs
  commands, spawns agents, or makes final decisions. *Output format:* exactly one of the four compact,
  paste-ready formats matching the job — `## Fast Brief`, `## Fast Triage`, `## Query Drafts`, or
  `## Compact Context`.
- **Pass/fail signal sketch** — PASS when the output uses the correct one-of-four format for the requested
  job, stays advisory (never claims to have fixed, validated, resolved, or decided), uses only prompt
  context, and returns a single result (leaf worker; no dispatch, no follow-up request). FAIL on the wrong
  format, a gate/consensus/approval decision, any mutation or dispatch, use of tools/web/filesystem, or
  more than one job per invocation. Note: this agent has no current Claude Layer 6 fixture, and both its
  candidate route (`haiku`/low, `CAP-Q3`) and its proposed `maxTurns` (CAR-010) remain probe/finalization-
  gated.

## Telemetry requirements

The non-interactive telemetry that each role's **later** route qualification (CAR-002/CAR-003) must
satisfy, stated as requirements only and derived from the recorded non-interactive-telemetry facts
`TEL-1…TEL-5`. Each field carries a **necessity label**: **mandatory**, **derived-from-configuration**,
or **platform-unavailable** (FR-026). **CAR-001 states these requirements; it builds no CAR-002 telemetry
capability profile** — capturing, scoring, and thresholding this telemetry against candidate tuples is
CAR-002/CAR-003 work, not this spike's.

*Statement class: `[INFERENCE]` composed from `TEL-1…TEL-5` (the necessity labels are requirements derived
from those cited facts); no new platform fact is asserted.*

### Mandatory (captured per candidate-tuple run)

From the `claude -p --output-format json` result payload (`TEL-1`):

- **`result`** (the role's text output) — needed to score the run against the fixture's pass/fail signal
  (see *Fixture backlog*).
- **session id** — transcript provenance and traceability across the candidate-tuple runs.
- **`usage` metadata** (input/output/cache token counts) — the cost basis; `TEL-4`'s OTel
  `claude_code.api_request` event enumerates `input_tokens`/`output_tokens`/`cache_read_tokens`/
  `cache_creation_tokens` at the same granularity.
- **`total_cost_usd`** — the cost half of cost-quality route qualification.
- **per-model cost breakdown** — attributes cost to the resolved model.
- **`structured_output`** — mandatory **only for roles whose `output_format` is structured**
  (`gate-validator`'s pass/fail JSON evidence most sharply), obtained by adding `--json-schema` (`TEL-1`);
  it proves the structured contract, not just prose.

The binding-proof field (from a companion surface, not the top-level `-p` result body):

- **`resolvedModel`** (mandatory; sourced from the SubagentStart hook / Agent-tool response, `TEL-5`) —
  the field that **proves** which dated model the shipped alias actually resolved to at run time; it is
  the direct evidence for `CAP-Q1…CAP-Q4`. Because it can differ from the requested `model`, qualification
  MUST capture it and MUST NOT assume the alias binding.

### Derived-from-configuration (known from the dispatched tuple, not read back)

- **dispatched `model` alias and `effort`** — set by the fixture when it dispatches the candidate tuple, so
  they are recorded by construction. `effort` in particular is **never** present in the
  `-p --output-format json` result (`TEL-2`).
- **agent identity / `query_source`** (`main`/`subagent`/`auxiliary`) — known from which agent the fixture
  dispatched; surfaced out-of-band as the OTel `claude_code.cost.usage` `agent.name`/`query_source`
  attributes (`TEL-3`), not the `-p` result.
- **`speed` / fast mode** — a session-level Opus configuration orthogonal to per-agent route policy (fast
  mode is not a subagent frontmatter field, `FST-3`/`PLG-1`); derived from the session config, not a
  per-agent telemetry value.

### Platform-unavailable on the `-p --output-format json` result surface

These MUST NOT be asserted from the `-p` result; where needed they come only from a distinct channel
(OTel/hooks) or cannot be had:

- **effective reasoning effort actually applied** — never returned by the `-p` JSON result (`TEL-2`). It is
  knowable only as the *configured* value (derived-from-configuration, above) or observed out-of-band via
  the OTel `claude_code.cost.usage` `effort` attribute (`TEL-3`); qualification MUST NOT read it back from
  the `-p` result. This is the canonical never-returned / derived field.
- **per-subagent cost/effort/speed attribution** — the `-p` result gives `total_cost_usd` plus a
  per-*model* breakdown, but per-*subagent* attribution (`query_source`, `effort`, `speed`, `agent.name`)
  lives only on the OTel surface (`claude_code.cost.usage`, `TEL-3`), a channel distinct from the `-p` result.

### Per-role differentiators

- **Background analysts** (`codebase-analyst`, `domain-researcher`, `spec-context-analyst`;
  `background:true`) — per `TEL-5`, a background subagent's async-launch tool response carries
  `resolvedModel` but **no usage fields** (`status: async_launched`). Their cost/usage telemetry MUST be
  captured from the completed transcript or a non-background evaluation run, not the launch response;
  `resolvedModel` remains available at launch.
- **Structured-output roles** (`gate-validator`, and any role emitting JSON evidence) — `structured_output`
  via `--json-schema` is mandatory (above), not optional.
- **`autopilot-fast-helper`** — text-only, no tools; its qualification telemetry is the same mandatory `-p`
  result set (`result` / cost / `resolvedModel`) against the `haiku`/low candidate (`CAP-Q3`); no
  tool-call telemetry applies.

Again: CAR-001 records these requirements only and **builds no CAR-002 telemetry capability profile**.

## Layer 6 labeling

**Bare prompt emulation.** The current Layer 6 Claude evaluation path
(`tests/speckit-pro/layer6-efficiency/run-efficiency-benchmarks.py`) drives a **frontmatter-stripped
agent body piped to `claude -p --model <model>`** (with `-c model_reasoning_effort=<effort>`; the
`SWEEP_CONFIGS` model sweep) — see the *Route-policy surface inventory* (F) and the *Layer 6 Claude
fixture gap*. This is **bare prompt emulation**: it runs the instruction prose against a model but does
**not** reproduce the agent's real execution treatment.

Because it strips the frontmatter and dispatches a bare top-level `-p` prompt, the emulation omits:

- **the required tool surface** — the agent's `disallowedTools` denylist and allowed tools are not applied
  (a read-only analyst is not actually held read-only);
- **the mutation contract** — the read-only versus read-write boundary is not enforced;
- **the dispatch context** — a real run is a plugin-scoped subagent dispatched through the Agent tool /
  orchestrator (`speckit-pro:<name>`, `PLG-2`), not a bare `-p` prompt;
- **telemetry proof** — `resolvedModel` from the SubagentStart hook and per-tuple cost are not captured
  (see *Telemetry requirements*).

**`non_release_evidence`.** Accordingly, **all historical Layer 6 results are labeled
`non_release_evidence`** — including the two current Claude fixtures (`consensus-synthesizer`,
`gate-validator`) and the `results-codex/` smoke results. Bare prompt emulation is **smoke-only** evidence
(does the prose roughly work against a model), and it **cannot support a release** route decision.

**Lift condition (CAR-003 only).** This label is lifted **only** by a CAR-003 replay through the shared
materializer that dispatches each agent under its **exact treatment** — the required tool surface, the
mutation contract, the dispatch context, and telemetry proof (AC-1.7). **CAR-001 claims no such replay**
and performs none; it records the label and the lift condition only.

*Statement class: the description of the current path is a repository fact (observed from
`run-efficiency-benchmarks.py` at the pinned tag); the `non_release_evidence` labeling and the CAR-003 lift
condition are proposed SpecKit Pro policy `[POLICY]`. No platform fact or benchmark result is asserted.*

## Go / no-go handoff

The record's final section: the self-contained handoff to CAR-002. It **enumerates the six required
elements** (FR-022), records any mandatory fact left unverified within the single-run timebox as a no-go
item or `CAP-Qn` (FR-023, SC-005), and **depends on no CAR-002 (or later) result and claims no candidate
executable before capability probing** (FR-022, AC-1.5, SC-004).

> **Self-containment assertion (read first).** This handoff is composed entirely from the pinned comparator
> (`speckit-pro-v2.19.1`), the tracked repository tree, and cited official documentation. It consumes **no**
> CAR-002 result, and it asserts **no** candidate route is executable before the capability questions below
> are answered by probing. A CAR-002 implementer can freeze the executable candidate set from this record
> and manifest alone, without re-deriving any role contract or re-reading agent source (SC-004).

*Statement class: `[INFERENCE]`/`[POLICY]` — this section composes the cited facts and the manifest into a
handoff and states a go/no-go decision (proposed SpecKit Pro policy); it asserts no new platform fact.*

### The six required elements (FR-022)

1. **Provisional candidate-route manifest** — `docs/ai/research/claude-agent-route-candidate-manifest.json`
   (`provisional: true`): all twelve agents, `alias_universe` `[opus, sonnet, haiku, fable]`, the pinned
   immutable production comparator (`speckit-pro-v2.19.1`, commit `e343aa2e4ebcb2d48c501f285d7072cfd55722da`),
   and per-agent `candidate_routes` each carrying the shipped alias, the expected resolved model ID, and
   effort, with `project_level_eligibility` recorded separately from `environment_time_availability`
   (FR-015). Well-formed and schema-conformant (SC-008).
2. **Role-contract catalog** — the twelve `role_contract` objects (summary, mutation_boundary,
   output_format, repo-relative `source_ref`) in the manifest, plus the record's *Agent inventory* and
   *Codex helper source inventory*: eleven current Claude routes and the `autopilot-fast-helper` recorded
   absence (net-new twelfth agent, contract-equivalent-translated from the Codex source with a
   source-complete `platform_field_mapping`).
3. **Fixture backlog** — the record's *Fixture backlog*: twelve requirements-level entries (role contract to
   exercise, representative task types, required evidence, pass/fail signal sketch; FR-019), each resolvable
   from its manifest `fixture_backlog_ref`. No full fixture specifications — those are CAR-003.
4. **Telemetry requirements (FR-026)** — the record's *Telemetry requirements*: the necessity-labeled
   (mandatory / derived-from-configuration / platform-unavailable) non-interactive
   `claude -p --output-format json` fields each role's later qualification must satisfy, derived from
   `TEL-1…TEL-5`. CAR-001 states them only and builds no CAR-002 telemetry capability profile.
5. **Unresolved capability questions** — `CAP-Q1…CAP-Q6` (record *Capability questions* plus manifest
   `capability_questions`): the four alias-binding probes (`CAP-Q1` opus, `CAP-Q2` sonnet, `CAP-Q3` haiku,
   `CAP-Q4` fable + availability) and the two undocumented-behavior probes (`CAP-Q5` unavailable-model
   dispatch, `CAP-Q6` alias re-pointing execution-time manifestation).
6. **Go/no-go decision** — stated below.

### No-go items / mandatory facts unverified within the timebox (FR-023, SC-005)

Within the single autopilot run, every platform fact recordable from current official Anthropic
documentation was sourced, quoted, and dated (*Primary-source fact table*, access date 2026-07-14). The
facts that documentation does **not** settle — and that therefore remain unverified at run end — are carried
as capability questions, never as facts or assumptions, with zero silent gaps:

- **Alias-to-dated-ID environment-time bindings** — `CAP-Q1` (opus), `CAP-Q2` (sonnet), `CAP-Q3` (haiku),
  `CAP-Q4` (fable, including availability). The docs bind each alias only to a *floating* "latest-family"
  target, re-pointable by environment variables and provider allowlists (`ALS-repoint`, `RES-3`), so no
  alias-to-dated-ID binding is a settled fact.
- **Two undocumented dispatch behaviors** — `CAP-Q5` (unavailable-model dispatch: hard-error versus silent
  substitution) and `CAP-Q6` (execution-time manifestation of alias re-pointing).

No mandatory fact was dropped or left in a silent or unclassifiable state; each open item has a stable
`CAP-Qn` home, and the timebox was not extended to chase them (FR-023).

### Decision

- **GO — the baseline handoff is complete.** CAR-002 has everything it needs to design capability probes and
  then freeze the executable candidate set: the provisional manifest, the role-contract catalog, the
  candidate tuples (project-level eligibility recorded, environment-time availability probe-gated), the
  fixture backlog, the telemetry requirements, and the six capability questions — all dated and cited, with
  zero shipped-default change (SC-006).
- **NO-GO — no candidate is executable yet.** No candidate route may be treated as executable until its
  `CAP-Qn` is resolved by probing: each alias must be resolved to its dated model ID and confirmed available
  in the benchmark environment (`CAP-Q1…CAP-Q4`), and the two undocumented dispatch behaviors (`CAP-Q5`,
  `CAP-Q6`) must be probed before any CAR-003 fallback or route-stability design relies on them. `fable`
  remains an executor-class candidate, excluded only by recorded probe or contract evidence (FR-013), never
  by product-announcement status.

**No dependency on CAR-002 results; no executable claim before probing.** This handoff records candidate
*eligibility* and probe *needs* only. It depends on no CAR-002 (or later) result (SC-004) and asserts no
candidate route is executable before the capability questions above are answered (FR-022, AC-1.5).

# Phase 1 Data Model: `agent_route_candidate_manifest`

**Date**: 2026-07-14 | **Branch**: `car-001-candidate-route-baseline`

This document is the authoritative field-level specification of the JSON manifest
`docs/ai/research/claude-agent-route-candidate-manifest.json`. Because the
Clarify phase was intentionally skipped (the spec had zero clarification
markers), this data model fully specifies the schema that Clarify would otherwise
have refined — every AC-1.6 field per agent entry, the `schema_version`, and the
structural representation that distinguishes **project-level candidate
eligibility** from **environment-time availability**. The machine contract in
`contracts/agent-route-candidate-manifest.schema.json` formalizes exactly this
model; the two must stay in lockstep.

Design invariants: the manifest is the single source of machine data and the
record (`claude-agent-route-candidates.md`) the single source of evidence and
rationale; they cross-reference by `agent_name` and `agent_contract_id`, and no
machine datum has two authoritative homes — the record's explicitly labeled
read-only mirror tables (Agent inventory, hash triples) are permitted because
they are recomputable and drift-detectable, not second authoritative copies
(Constitution VI; §7 rule 9). All hashes are lowercase hex
sha256 computed with the Python 3.11+ standard library (FR-011, FR-025).

---

## 1. Top-level manifest object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string (semver `^\d+\.\d+\.\d+$`) | yes | Version of this manifest schema. Starts at `1.0.0`. Bumped by later CAR specs when the shape changes. |
| `manifest_kind` | string const `agent_route_candidate_manifest` | yes | Discriminator identifying the artifact kind. |
| `generated_at` | string (ISO-8601 date) | yes | Research/access date the manifest was produced (e.g. `2026-07-14`). |
| `provisional` | boolean const `true` | yes | Marks this as provisional research output, not the plugin-owned route-policy manifest (CAR-006 owns that). |
| `immutable_production_comparator` | object | yes | The pinned baseline identity — see §2. |
| `alias_universe` | array[string] | yes | The four documented candidate aliases: `["opus","sonnet","haiku","fable"]` (FR-012). Closed set. |
| `capability_questions` | array[object] | yes | The `CAP-Qn` questions the manifest references — see §6. May be empty only if every mandatory fact was verified (rare). |
| `agents` | object (map: `agent_name` → `agent_route_entry`) | yes | Exactly the twelve named agents (§3). Keys are the agent names. |

**Cardinality rule (SC-001)**: `agents` MUST contain exactly twelve keys — the
eleven current Claude agents plus `autopilot-fast-helper` — with zero agents
missing any required field.

---

## 2. `immutable_production_comparator` (FR-009, Design Q3)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `release_tag` | string | yes | The pinned release tag: `speckit-pro-v2.19.1` (latest published at research time). |
| `commit_sha` | string (40-hex) | yes | The tag's commit SHA: `e343aa2e4ebcb2d48c501f285d7072cfd55722da`. |
| `pin_rationale` | string | yes | Why this tag is the comparator (consumer-installable identity; reproducible). |
| `reconciliation_note` | string | optional | Records the 2.19.0 → 2.19.1 reconciliation: 2.19.0 was the 2026-07-13 scaffold snapshot; 2.19.1 is the latest published at research time; `agents/` and `codex-agents/` are byte-identical between the two, so all tuples and hashes are unchanged. |

The comparator holds the *release* identity. Each agent's *per-agent* frontmatter
route tuple and content hashes live in that agent's entry (§3
`immutable_production_route` and `agent_file_hashes`) so drift is detectable at
agent granularity.

---

## 3. `agent_route_entry` (per agent) — FR-014, AC-1.6

Each value in `agents` is an object with the following fields. Every field is
required for all twelve agents unless the "Required" column says otherwise.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_name` | string | yes | Canonical agent name; MUST equal the map key. |
| `agent_contract_id` | string | yes | Stable identifier for this agent's role contract; the cross-reference key the record and downstream specs bind to. Stable across pure route changes. |
| `role_contract` | object | yes | The role-specific contract — see §3.1. |
| `immutable_production_route` | object \| null | yes (nullable) | The current shipped route (`{model, effort}`) for the eleven current agents; `null` for `autopilot-fast-helper` (FR-010). When `null`, `production_route_recorded_absence` MUST be `true`. |
| `production_route_recorded_absence` | boolean | yes | `true` only for the net-new helper (explicit absence, not omission); `false` for the eleven current agents. |
| `agent_file_hashes` | object | yes | Instruction and full-file hashes — see §3.2. |
| `candidate_routes` | array[`candidate_route_tuple`] | yes | ≥1 candidate tuple (§4). Alias-based (FR-012). |
| `required_capabilities` | object | yes | Model/modality/subagent-field/tool/skill/client capabilities the role requires — see §3.3. |
| `candidate_rationale` | string | yes | Why this candidate set fits the role (may also be recorded per tuple in §4). |
| `known_incompatibilities` | array[object] | yes | Recorded incompatibilities; each `{subject, reason, evidence_ref}`. Empty array allowed, but the field MUST be present. |
| `required_qualification_artifacts` | array[string] | yes | The evidence CAR-003 must produce before any candidate is called executable (e.g. fixture pass records, transcript captures). |
| `invalidation_triggers` | array[string] | yes | Conditions that invalidate this entry. MUST be candidate-specific and actionable, not boilerplate (FR-014): for every distinct alias in `candidate_routes` the array MUST carry a trigger for that alias re-pointing to a new resolved model ID (e.g. "alias `opus` re-points to a new resolved model ID"), and MUST carry the agent's comparator-drift trigger (e.g. "agent frontmatter route drifts from the comparator hash"). `minItems` 1 in the contract; the per-alias coverage is enforced by the quickstart check (§7 rule 10), not by JSON Schema. |
| `fixture_backlog_ref` | string | yes | Cross-reference to the requirements-level fixture-backlog entry in the record (FR-019); the manifest does not inline full fixture specs. |

### 3.1 `role_contract`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `summary` | string | yes | One-to-three-sentence statement of the agent's bounded job. |
| `mutation_boundary` | string | yes | What the agent may and may not mutate (read-only vs. write; tool denylist posture). Load-bearing for the helper (FR-017) and the read-only analysts. |
| `output_format` | string | yes | The required output contract (e.g. structured summary, JSON evidence, edits-only). |
| `source_ref` | string | yes | Repo-relative reference to where the contract is derived from (the agent `.md`, or the Codex toml for the helper). No absolute paths. |

### 3.2 `agent_file_hashes` (FR-011, SC-007)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `instruction_sha256` | string (64-hex) | yes | sha256 over the **frontmatter-stripped** agent body. A pure frontmatter route change MUST leave this unchanged (SC-007). |
| `full_file_sha256` | string (64-hex) | yes | sha256 over the full agent file (frontmatter included), for drift detection. |
| `hash_source` | string enum `claude-agent-md` \| `codex-toml-translation` | yes | For the eleven current agents, `claude-agent-md`. For `autopilot-fast-helper` (no Claude `.md` exists), `codex-toml-translation`: the instruction identity is computed over the contract-equivalent translated body, and `full_file_sha256` records the sha256 of the source Codex toml for provenance. |

**Hash input — source and boundary (FR-010, FR-011, SC-007).** All three hashes
MUST be computed over the agent file's bytes **as published at the pinned
comparator tag** (`speckit-pro-v2.19.1`, commit
`e343aa2e4ebcb2d48c501f285d7072cfd55722da`), never the working-tree copy, so the
recorded identity provably represents the immutable comparator and is
reproducible from the tag. **Frontmatter** is the leading YAML block delimited by
the first pair of `---` fence lines (the file's opening `---` line and its
closing `---` line); the **instruction body** is everything after that closing
fence line, hashed verbatim — byte-for-byte, no normalization of whitespace,
line endings, or content (Design Q4, which rejected a normalization policy as
YAGNI). `full_file_sha256` covers the whole file including the frontmatter block.

### 3.3 `required_capabilities` (FR-014)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | array[string] | yes | Model-class requirements the role needs (e.g. reasoning depth); phrased as requirements, not a pinned model. |
| `modality` | array[string] | yes | Required modalities (e.g. text; vision if the role needs it). |
| `subagent_fields` | array[string] | yes | Required subagent configuration fields (e.g. `model`, `effort`, tool scoping). `effort` is the subagent frontmatter field (record `SUB-fields`); `model_reasoning_effort` is only the Layer 6 `claude -p` CLI key, not a frontmatter field. Each is a fact-or-question per the record's classification. |
| `tools` | array[string] | yes | Required tool surface (or the denylist posture for read-only roles). |
| `skills` | array[string] | yes | Required skill access (empty array if none). |
| `client` | array[string] | yes | Required client capabilities (e.g. non-interactive `claude -p`, plugin-agent field support). |

---

## 4. `candidate_route_tuple` (FR-012, FR-015, FR-016) — the eligibility/availability split

Each element of `candidate_routes` is one `(alias, expected resolved model ID,
effort)` combination, with **project-level eligibility recorded separately from
environment-time availability** (FR-015). This is the structural representation
the skipped Clarify phase would have pinned down.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alias` | string enum `opus`\|`sonnet`\|`haiku`\|`fable` | yes | One of the four documented aliases (FR-012). No legacy dated snapshots as separate candidates. |
| `expected_resolved_model_id` | string \| null | yes (nullable) | The dated model ID the alias is expected to resolve to per official docs. `null` when the docs do not bind the alias at research time — in which case `availability.binding_question_ref` MUST point to a `CAP-Qn` (Edge Cases). |
| `effort` | string enum `low`\|`medium`\|`high`\|`xhigh`\|`max` | yes | The effort level for this tuple, drawn from the documented subagent effort levels (record `EFF-1`: `low`/`medium`/`high`/`xhigh`/`max`). Documented-fact or proposed-policy per the record's labeling. |
| `project_level_eligibility` | object | yes | Recorded-now eligibility from role fit — see §4.1. |
| `environment_time_availability` | object | yes | Explicitly deferred to CAR-002 probing — see §4.2. |
| `tuple_rationale` | string | optional | Why this specific tuple is a candidate for the role. |

### 4.1 `project_level_eligibility` (recorded now, from the role contract)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eligible` | boolean | yes | Whether the tuple is eligible for the role at the project (contract) level, independent of any environment. |
| `basis` | string | yes | The role-fit basis for eligibility (e.g. "executor-class role; `fable` is candidate-eligible for task-execution agents", FR-013). |
| `evidence_class` | string enum `fact`\|`inference`\|`proposed_policy`\|`assumption` | yes | The statement class backing this eligibility (SC-003). |

### 4.2 `environment_time_availability` (deferred to CAR-002)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | string const `probe_required` | yes | This spike never resolves availability; it is always a CAR-002 probe outcome (AC-1.4, AC-1.5). No candidate is claimed executable before probing (FR-022). |
| `probe_question_ref` | string (`CAP-Qn`) | yes | The capability question CAR-002 answers to establish availability. |
| `binding_question_ref` | string (`CAP-Qn`) | yes | The capability question that resolves the alias-to-ID binding. Required on **every** candidate tuple: in this provisional manifest every `expected_resolved_model_id` is a recorded `[INFERENCE]` gated on a `CAP-Qn` (the docs bind each alias only to a floating "latest-family" target, never a settled dated ID), so no tuple's binding is officially fixed. The contract requires it unconditionally (§7 rule 6). |

**Exclusion rule (FR-016)**: a model or effort is excluded from a candidate set
only for recorded incompatibility (`known_incompatibilities`), recorded contract
failure, or predeclared dominance evidence — never by product-announcement
status. `fable` therefore stays in executor-class candidate sets with an
invalidation trigger and a capability question rather than being dropped
(FR-013, Edge Cases).

**Effort applicability (EFF-1)**: the documented subagent effort levels are
model-dependent (record `EFF-1`: "available levels depend on the model"), so a
tuple's `effort` is not established as valid by alias resolution alone. Each
alias-binding probe (`CAP-Q1`–`CAP-Q4`) therefore also confirms the resolved
model accepts and applies the tuple's effort level; a resolved model that
rejects the tuple's effort is a recorded incompatibility (FR-016), not a silent
drop.

---

## 5. `autopilot-fast-helper` entry specifics (FR-017, FR-018, Design Q7)

The twelfth entry follows the same `agent_route_entry` shape with these
constraints:

- `immutable_production_route` = `null`; `production_route_recorded_absence` =
  `true` (no current Claude production route).
- `role_contract` is a **contract-equivalent translation** of
  `speckit-pro/codex-agents/autopilot-fast-helper.toml`: role prose, the four
  bounded jobs, hard rules, and output formats carried over.
- The entry MUST carry an explicit **platform-field mapping table** (recorded in
  the manifest as `platform_field_mapping`, an array of
  `{codex_field, claude_equivalent, evidence_class, note}`), mapping e.g.
  `sandbox_mode: read-only` → a comprehensive no-tool `disallowedTools` denylist (prompt-context-only; stricter than the analysts' read-only denylist) and
  `codex-spark` → `haiku` + explicit low effort (starting hypotheses, labeled).
  The table MUST be **source-complete** (FR-017): every field in
  `speckit-pro/codex-agents/autopilot-fast-helper.toml` — `model`, `sandbox_mode`,
  and the `developer_instructions` contract content (role prose, bounded jobs,
  hard rules, output formats) — appears as a row, either mapped to a Claude
  equivalent or explicitly marked no-equivalent (`evidence_class: proposed_policy`
  per FR-018); no source field is silently dropped. Because JSON Schema cannot
  read the source toml, this source-exhaustiveness is a quickstart/review-enforced
  authoring rule (like the §7 rule 10 invalidation-trigger coverage), not a schema
  constraint.
- Claude-only fields with no Codex equivalent (e.g. `maxTurns`) appear with a
  proposed value and `evidence_class: proposed_policy` labeled "proposed SpecKit
  Pro policy", deferred to CAR-010 (FR-018).

`platform_field_mapping` is a required field **only** on the
`autopilot-fast-helper` entry; it is absent on the eleven current agents.

---

## 6. `capability_question` (FR-021) — referenced by the manifest, authored in the record

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string (`^CAP-Q\d+$`) | yes | Stable ID (`CAP-Q1…CAP-Qn`). |
| `question` | string | yes | The unresolved question handed to CAR-002 for probe design. |
| `blocks` | array[string] | yes | What the question blocks (e.g. which agents' availability or which alias binding). |

The full prose lives in the record's dedicated capability-question section; the
manifest carries the machine-referenceable stubs so tuples can point at them by
`id`.

---

## 7. Validation rules (enforced by the contract + quickstart checks)

1. **Twelve-agent coverage (SC-001)**: `agents` has exactly the twelve named
   keys; each entry has every required field non-empty (empty arrays permitted
   only where §3 marks them so).
2. **Alias closure (FR-012)**: every `candidate_routes[].alias` ∈
   `{opus, sonnet, haiku, fable}`; no other candidate identifiers exist.
3. **Absence integrity (FR-010)**: exactly one entry
   (`autopilot-fast-helper`) has `immutable_production_route == null` and
   `production_route_recorded_absence == true`; the other eleven have a non-null
   route and `false`.
4. **Hash integrity (FR-010, FR-011, SC-007)**: `instruction_sha256` and
   `full_file_sha256` are 64-hex; all hashes are computed over the agent file's
   bytes at the pinned comparator tag (not the working tree) using the §3.2
   frontmatter boundary; for the eleven current agents recomputing sha256 over
   the frontmatter-stripped tag body reproduces `instruction_sha256`, and a pure
   frontmatter route change does not change it.
5. **Eligibility/availability split (FR-015)**: every tuple has both
   `project_level_eligibility` and `environment_time_availability`;
   `environment_time_availability.status` is always `probe_required`.
6. **Binding-question rule (Edge Cases)**: every candidate tuple's
   `environment_time_availability.binding_question_ref` references an existing
   `CAP-Qn`. Because every `expected_resolved_model_id` in this provisional
   manifest is an `[INFERENCE]` gated on a capability question (no alias is bound
   to a settled dated ID at research time), the contract requires
   `binding_question_ref` **unconditionally** on `candidate_route_tuple`, not
   only when the expected ID is `null`.
7. **No-executable-claim (FR-022)**: no field asserts a candidate is executable;
   executability is always gated behind `probe_required` + qualification
   artifacts.
8. **Comparator pin (FR-009)**: `immutable_production_comparator.release_tag`
   and `commit_sha` are present and match the pinned `2.19.1` identity.
9. **Cross-reference integrity (Constitution VI)**: every `agent_contract_id`,
   `fixture_backlog_ref`, and `CAP-Qn` referenced in the manifest resolves to a
   section in the record; no machine datum has two *authoritative* homes. The
   record's *Agent inventory* route tuples and *Agent-file hash triples* are
   explicit read-only **mirrors** of the authoritative manifest values (each
   table states the mirror direction) and are kept drift-detectable by
   recomputation from the pinned tag (rule 4, quickstart V5), not second
   authoritative copies.
10. **Invalidation-trigger coverage (FR-014)**: `invalidation_triggers` is
    candidate-specific and actionable — for every distinct alias in
    `candidate_routes` there is a trigger for that alias re-pointing, plus the
    agent's comparator-drift trigger; a single generic/boilerplate trigger fails
    this rule. Enforced by the quickstart check (candidate aliases cannot be
    cross-referenced against free-text triggers in JSON Schema).

---

## 8. Spec Key Entities → representation map

| Spec entity | Representation |
|-------------|----------------|
| Research Record | The Markdown deliverable `docs/ai/research/claude-agent-route-candidates.md` (evidence, labels, fixture backlog, capability questions, go/no-go handoff). Not part of this JSON schema. |
| Candidate Route Manifest | The top-level object (§1). |
| Agent Route Entry | `agent_route_entry` (§3), one per agent under `agents`. |
| Candidate Route Tuple | `candidate_route_tuple` (§4). |
| Primary-Source Fact Row | Authored in the record's fact table (URL + access date + verbatim quote); the manifest references facts via `evidence_class` labels and `evidence_ref` strings, not by inlining the quotes. |
| Capability Question | `capability_question` (§6), referenced by tuples via `probe_question_ref` / `binding_question_ref`. |
| Immutable Production Comparator | `immutable_production_comparator` (§2) plus per-agent `immutable_production_route` + `agent_file_hashes` (§3). |
| Fixture Backlog Entry | Authored in the record (requirements-level, FR-019); referenced from each entry by `fixture_backlog_ref`. |
| autopilot-fast-helper Contract | The twelfth `agent_route_entry` with `platform_field_mapping` and `production_route_recorded_absence == true` (§5). |

---

## 9. Illustrative shape (non-normative excerpt)

The following abbreviated fragment shows structure only; real values (resolved
model IDs, hashes, quotes) are produced during implementation. Field names and
nesting here are normative; the values are placeholders.

```json
{
  "schema_version": "1.0.0",
  "manifest_kind": "agent_route_candidate_manifest",
  "generated_at": "2026-07-14",
  "provisional": true,
  "immutable_production_comparator": {
    "release_tag": "speckit-pro-v2.19.1",
    "commit_sha": "e343aa2e4ebcb2d48c501f285d7072cfd55722da",
    "pin_rationale": "Latest published release at research time; consumer-installable, reproducible from the tag.",
    "reconciliation_note": "2.19.0 was the 2026-07-13 scaffold snapshot; agents/ and codex-agents/ are byte-identical between 2.19.0 and 2.19.1, so all tuples and hashes are unchanged."
  },
  "alias_universe": ["opus", "sonnet", "haiku", "fable"],
  "capability_questions": [
    { "id": "CAP-Q1", "question": "Does official doc bind alias 'opus' to a dated model ID at research time?", "blocks": ["expected_resolved_model_id for all opus tuples"] }
  ],
  "agents": {
    "phase-executor": {
      "agent_name": "phase-executor",
      "agent_contract_id": "car.phase-executor.v1",
      "role_contract": {
        "summary": "Executes a single SpecKit phase via the Skill tool.",
        "mutation_boundary": "Writes phase artifacts; no cross-spec writes.",
        "output_format": "Structured phase-result summary.",
        "source_ref": "speckit-pro/agents/phase-executor.md"
      },
      "immutable_production_route": { "model": "opus", "effort": "max" },
      "production_route_recorded_absence": false,
      "agent_file_hashes": {
        "instruction_sha256": "<64-hex>",
        "full_file_sha256": "<64-hex>",
        "hash_source": "claude-agent-md"
      },
      "candidate_routes": [
        {
          "alias": "opus",
          "expected_resolved_model_id": null,
          "effort": "max",
          "project_level_eligibility": {
            "eligible": true,
            "basis": "Executor-class role; heavy architectural reasoning.",
            "evidence_class": "inference"
          },
          "environment_time_availability": {
            "status": "probe_required",
            "probe_question_ref": "CAP-Q2",
            "binding_question_ref": "CAP-Q1"
          },
          "tuple_rationale": "Matches shipped opus/max production route."
        }
      ],
      "required_capabilities": {
        "model": ["deep-reasoning"],
        "modality": ["text"],
        "subagent_fields": ["model", "effort"],
        "tools": ["Skill", "Read", "Write", "Bash"],
        "skills": ["speckit-*"],
        "client": ["claude -p non-interactive"]
      },
      "candidate_rationale": "Executor class; fable candidate-eligible pending probe.",
      "known_incompatibilities": [],
      "required_qualification_artifacts": ["CAR-003 fixture pass record"],
      "invalidation_triggers": [
        "alias 'opus' re-points to a new resolved model ID",
        "phase-executor frontmatter route drifts from comparator hash"
      ],
      "fixture_backlog_ref": "record#fixture-backlog-phase-executor"
    }
  }
}
```

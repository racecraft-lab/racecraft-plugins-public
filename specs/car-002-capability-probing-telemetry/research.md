# Phase 0 Research: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

This document resolves every decision the Clarify phase deferred to Plan, plus the
technology-choice questions surfaced by the Technical Context. Each entry cites the
binding spec Assumptions / FR it grounds against. No `[NEEDS CLARIFICATION]` remains.

Ground rules carried from the spec and `docs/ai/specs/agent-routing-parity-contract.md`:
platform facts come only from `code.claude.com/docs/**` or `platform.claude.com/docs/**`;
probes narrow availability but never establish a platform fact (FR-026); missing or
conflicting documentation fails closed (FR-027).

---

## R1 — Exact `tuple_id` derivation format

**Decision**: `tuple_id = "<model>__<effort>"`, a pure function of the resolving
CAR-001 candidate route's `model_selector.requested_value` and
`effort_selector.requested_value`, lowercase, joined by a double underscore. If
`effort_selector.requested_value` is JSON `null`, the effort segment is the literal
`none`. The 37 CAR-001 candidate routes reduce to exactly these 6 tuple IDs:
`opus__max`, `sonnet__max`, `fable__max`, `haiku__max`, `haiku__low`, `sonnet__low`.

**Rationale**: The spec fixes the join as a pure function of the manifest's
`model_selector`/`effort_selector` fields keyed by a deterministic, computable
`tuple_id` (FR-004; Key Entities "(model, effort) tuple"; Assumptions "ID conventions").
Verified against the committed manifest: grouping all 37 `candidate_routes` by
`(model_selector.requested_value, effort_selector.requested_value)` yields exactly 6
groups (opus__max ×11, sonnet__max ×11, fable__max ×5, haiku__max ×8, haiku__low ×1,
sonnet__low ×1; total 37). The double-underscore separator is unambiguous because
alias and effort tokens are single lowercase words with no internal underscores. The
map is **derived on demand, never persisted** — the snapshot stores per-tuple evidence
keyed by `tuple_id`, and the 37→tuple join is recomputed from the committed manifest
(constitution VI; FR-004; SC-005 forbids a persisted `candidate_route_id`→`tuple_id` map).

**Alternatives considered**: (a) `<model>-<effort>` single hyphen — rejected, hyphen
already separates the CAR-001 ID number segments and reads ambiguously; (b) hashing the
pair — rejected, opaque and unreviewable, defeats SC-007's "read without executing
Python"; (c) persisting the per-route map in the snapshot — rejected by FR-004/SC-005
(constitution VI, drift risk).

---

## R2 — Record-class enum field name and value casing (exact-treatment `$def`)

**Decision**: Field name `record_class` (snake_case instance field) on the
`exactTreatmentReplay` `$def`, with enum values `["success", "null", "unavailable",
"misdelivery"]` (lowercase string literals). The value `"null"` is the string
`"null"` naming the class, not JSON `null`.

**Rationale**: The spec deliberately uses the plain phrase "record class" and lists the
four classes as `success, null, unavailable, misdelivery` (US4; FR-024; FR-025; SC-003).
Instance-level fields in the CAR-001 schema family are snake_case (`schema_version`,
`snapshot_id`, `source_class`), so `record_class` matches local convention; the CAR-001
`telemetry.source_class` field is the direct precedent for a `*_class` enum. Lowercase
string values match every existing enum in `agent-route-candidate-manifest.schema.json`.

**Alternatives considered**: (a) `recordClass` camelCase — rejected, camelCase is
reserved for `$def` **names**, not instance fields (Tech Stack; CAR-001 convention);
(b) `outcome_class` / `class` — rejected, `class` is a reserved word in consumers and
`record_class` is the spec's own phrasing.

---

## R3 — One-shot empirical confirmation of raw `--output-format json` key spellings

**Decision**: Before the `claude_capabilities.py` parser is finalized, the operator runs
**one** `claude -p --output-format json` canary invocation, captures raw stdout, and
confirms the exact key spellings the parser depends on — in particular the top-level
camelCase `modelUsage` key (not the Python binding's snake_case `model_usage`, which
does not govern CLI stdout) and its sub-fields `inputTokens`, `outputTokens`,
`cacheReadInputTokens`, `cacheCreationInputTokens`, `contextWindow`, `costUSD`, plus the
snake_case `usage.*` and `total_cost_usd`/`num_turns`/`duration_ms` fields. This
confirmation is step 1 of the operator probe run (see quickstart.md) and gates parser
finalization. Any field the confirmation has not run against is labeled `observation`,
never certified fact.

**Rationale**: Spec Assumptions "Telemetry field grounding" states no canonical page
prints a literal full payload, so byte-for-byte key-spelling equivalence between raw CLI
stdout and the documented `SDKResultMessage` type is a one-shot empirical confirmation
carried to Plan (FR-019/FR-027). The confirmation is cheap (one canary already required
for CAP-Q1 ID binding) and removes the single largest parser risk before code is frozen.

**Alternatives considered**: (a) Trust the TypeScript type docs and skip confirmation —
rejected, the docs govern the SDK type, not raw CLI stdout, and FR-027 forbids assuming;
(b) Defer confirmation to CAR-003 — rejected, the parser cannot be written correctly or
tested deterministically against a fixture whose key spellings are unverified.

---

## R4 — Probe-integrity controls (carried from Clarify Session 1)

**Decision**: Two integrity controls are built into `claude_capabilities.py`:
1. **Requested-vs-observed cross-check** — for every unavailable-model probe, the writer
   compares the requested unavailable model ID against the model key(s) present in the
   result message's `modelUsage`. If `modelUsage` reports a *different* model than the
   requested unavailable ID, a soft remap / fallback occurred and the observation is
   flagged (the interfering-configuration edge case), so bare-platform behavior is not
   misread as availability.
2. **No preempting per-invocation model on the subagent surface** — the subagent-frontmatter
   probe MUST NOT pass a per-invocation `--model` (or any per-call model override) that
   would preempt the frontmatter value under test. The subagent dispatch is a plain
   `claude -p` with an `@agent-<probe-name>` mention only; the agent file's frontmatter
   model is the value being probed.

**Rationale**: These are the probe-integrity details the Clarify consensus recorded
(spec FR-009/FR-010 and Assumptions "Unavailable-model probe mechanism": the outcome
path — soft remap via `modelUsage`, hard rejection, or silent fallback — is exactly the
probe's observation to capture; a preempting per-call model would make the frontmatter
test meaningless). The `modelUsage` cross-check is also how CAP-Q6 alias re-pointing is
detected downstream (route-change detection rule, R11).

**Alternatives considered**: (a) Trust exit code alone for the unavailable probe —
rejected, a zero exit with a silent fallback would be misread as availability;
(b) pass `--model <unavailable>` on the subagent call as belt-and-suspenders — rejected,
it preempts the frontmatter surface CAP-Q5 actually gates (FR-009).

---

## R5 — Schema publication: one file, `$def` naming, shared primitives, raw-evidence shape

**Decision**: One JSON Schema (draft 2020-12) file, shipped at
`docs/ai/research/claude-trace-contract.schema.json` (design draft in
`contracts/claude-trace-contract.schema.json`). Top-level `$id`,
`$schema: https://json-schema.org/draft/2020-12/schema`, `additionalProperties: false`
throughout. Four record `$defs`, camelCase names: `runtimeCapabilitySnapshot`,
`telemetryProfile`, `routeResolution`, `exactTreatmentReplay`. Shared primitive `$defs`
reused from the CAR-001 conventions: `sha256` (`^[0-9a-f]{64}$`), `nullableString`
(`["string","null"]`), plus a CAR-002-specific `rawEvidence` `$def`. Every record carries
an instance-level `schema_version` const `"1.0.0"` (FR-015). Validated by hand-rolled
standard-library logic in `claude_trace_schema.py` — no third-party `jsonschema` — mirroring
`validate_manifest` in `tests/speckit-pro/unit/test-agent-route-research-parity.py`
(`require_exact_keys`, `schema_keys`, `require_sha256`, `require_utc_timestamp`).

`rawEvidence` `$def`: `{ raw_output: <string>, raw_output_sha256: <sha256>, sanitization:
const "home_paths_and_session_ids_normalized_utf8" }`. It stores the **full** sanitized `--output-format
json` stdout committed verbatim as a string (not a parsed object), deliberately distinct
from CAR-001's 700-char-capped `boundedExtract` because the ratified Q7 decision stores
the whole payload (FR-012/FR-013; Key Entities "Raw probe evidence").

**Rationale**: Reuses the exact CAR-001 manifest-schema + stdlib-validator pattern (Q5;
FR-015/FR-016/FR-017) so Codex-side parity work reads the same platform-neutral contract
without executing Python (SC-007). `$def` names are camelCase and instance fields
snake_case, matching CAR-001. The `schema_version` starts its own line at `1.0.0`,
independent of CAR-001's `2.0.0` (Assumptions "Contract versioning").

**Alternatives considered**: (a) Four separate schema files — rejected, shared identity
fields would duplicate or need cross-file `$ref`s (design concept Q5 alt);
(b) third-party `jsonschema` — rejected by constitution II / FR-016 (stdlib only);
(c) reuse `boundedExtract` for raw evidence — rejected, the 700-char cap truncates the
full payload the replay validation needs (Q7).

---

## R6 — Effort-configuration surface and the silent-clamp avoidance

**Decision**: The effort surface is the documented `--effort` CLI flag
(`code.claude.com/docs/en/cli-reference` — session-scoped, non-persistent), with the
`effortLevel` setting and `CLAUDE_CODE_EFFORT_LEVEL` env var as documented alternatives.
The probe matrix uses the per-model-supported subset of `low`/`medium`/`high`/`xhigh`/`max`
(the `ultracode` session mode is excluded — it is not an effort level). The
effort-acceptance probe runs in **plain-text `--print`** (which warns, naming requested vs
applied levels) rather than JSON output (which clamps an org effort cap silently), or
records an explicit no-org-cap assumption. Per-(model, effort) acceptance is labeled
`observation`, never certification.

**Rationale**: Directly pinned by spec Assumptions "Effort-configuration surface" and the
"Silently-clamped effort under JSON output" edge case (`code.claude.com/docs/en/model-config`).
The FR-027 labeled-inference fork does not fire for the surface itself (it is documented),
only for observed per-(model, effort) acceptance under silent-clamp-capable output. This
resolves design concept Open Question 1 (the effort-configuration surface) with a
documented fact.

**Alternatives considered**: (a) Probe effort acceptance under `--output-format json` for
uniformity — rejected, the org cap clamps silently and would certify a level that was not
actually applied; (b) treat `--effort` as undocumented and label the whole method as
inference — rejected, the flag is documented, so only residual acceptance is labeled.

---

## R7 — Authentication mode detection and the models endpoint

**Decision**: Each run records the operator environment's authentication mode from
documented signals: `ANTHROPIC_API_KEY` or `ANTHROPIC_AUTH_TOKEN` present ⇒ `api_key`;
otherwise ⇒ `subscription`. `GET /v1/models` is called **only** in `api_key` mode; its
returned dated IDs and per-model effort capability flags are stored as *corroborating*
evidence (the endpoint documents no alias field, and API-catalog presence does not prove
coding-client availability). In `subscription` mode or any unreachable case, the endpoint's
absence is recorded as a gap, not a failure.

**Rationale**: Verbatim from FR-014 and design concept Open Question 2 (environment-time
fact). Fail-closed: an unreachable endpoint is a recorded gap (FR-027), never a run
failure (edge case "API models endpoint unreachable").

**Alternatives considered**: (a) Always call the endpoint — rejected, it is unreachable
under subscription auth and would fail the run; (b) treat catalog presence as
alias-establishing — rejected by FR-026 (probes narrow, never establish).

---

## R8 — Fixed canary prompt text and hash

**Decision**: A single canary prompt is used identically across all probes in one
snapshot: `Reply with the single word: ok` (exact UTF-8 bytes, no trailing newline). Its
SHA-256 is computed over those exact bytes and stored in snapshot metadata alongside the
per-payload raw-evidence hashes.

**Rationale**: Pinned by spec Assumptions "Fixed canary" and design concept Open Question 3.
Content is measurement-irrelevant — alias→ID binding and config acceptance come from the
`--output-format json` metadata, not the reply — so only byte-invariance across a snapshot
is contractual (FR-005). Recording the text and hash makes the invariant verifiable.

**Alternatives considered**: (a) Per-probe prompts — rejected, breaks the FR-005
one-identical-canary invariant; (b) empty prompt — rejected, some surfaces require
non-empty input and the reply is a useful liveness signal.

---

## R9 — Sanitization to `<home>` and SHA-256 over sanitized bytes

**Decision**: Before the snapshot is written, every raw `--output-format json` payload has
home/user paths normalized to the `<home>` token per the existing release-readiness
sanitization convention. The SHA-256 stored in each `rawEvidence` is computed over the
**exact sanitized UTF-8 bytes** of the string committed verbatim (not a parsed-and-reserialized
object), so the hash reproduces from committed bytes. No unsanitized payload — no absolute
home/user path, no machine-local session path — is ever committed. The privacy scan
(`tests/speckit-pro/unit/test-privacy-scan.py`) is the enforcing gate.

**Rationale**: Pinned by FR-012/FR-013 and the "Malformed probe payload" edge case. Storing
verbatim string bytes (rather than a reparsed object) is what makes the hash reproducible
and the replay byte-exact (Q7). Sanitizing before write means an unsanitized payload can
never reach the working tree.

**Alternatives considered**: (a) Hash the parsed object — rejected, reserialization changes
bytes and breaks hash reproduction; (b) store unsanitized bytes and sanitize at read —
rejected, the privacy scan rejects committed absolute paths and it leaks machine layout.

---

## R10 — WP1 reviewable-LOC sizing: mechanical estimator run + G5 escalation

**Decision**: Record the mechanical `estimate-reviewable-loc` output for the whole feature
and carry the WP1 real-LOC conflict to G5 without re-slicing.

Mechanical output (run against `specs/car-002-capability-probing-telemetry/plan.md`):

```json
{"tool":"estimate-reviewable-loc","status":"pass","projected":0,
 "declared_files":{"production":0,"new":11,"modified":2,"total_entries":13},
 "greenfield":false,
 "thresholds":{"warn":400,"block":800,"greenfield_multiplier":1.5,"base_warn":400,"base_block":800}}
```

**Rationale**: The estimator's `is_production_file` counts a file only when its path starts
with `src/`/`app/`/`lib/`/`scripts/` or ends in `.ts/.tsx/.js/.jsx/.mjs/.cjs/.sql`. Every
CAR-002 file is test-tree Python (`tests/speckit-pro/**.py`) or research JSON
(`docs/ai/research/**.json`), so `production` is 0 and `projected` is 0 (`status: pass`).
This is a real blind spot, not a green light: hand-estimating WP1's authored surface
(validator ~240-300 + probe tool ~240-320 + schema JSON ~240-320 + WP1 unit-test portion
~140-200) gives **~550-820 reviewable LOC**, which breaches the 400 warn ceiling and may
approach the 800 block ceiling under the PR-time diff-mode gate that counts real lines.

Per spec "Split decision" and the workflow instruction, this is recorded for **G5
escalation** and **not** silently re-sliced — the 3-WP boundary is Clarify-ratified and
WP1's contents are atomically coupled (FR-015/FR-016/FR-028 mandate one schema, one
validator, one registration; FR-023's fail-closed writer cannot be built or tested without
the schema). G5 chooses between (1) a single WP1 PR with a documented over-ceiling
reviewability exception (recommended) or (2) PRSG file-level review units inside the one
WP. See plan.md "WP1 sizing".

**Alternatives considered**: (a) Re-slice WP1 into two work packages — rejected, the split
is ratified and re-slicing here is explicitly forbidden; (b) trust the mechanical
`projected: 0` and declare WP1 safe — rejected, it under-counts the true reviewer burden.

---

## R11 — CAP-Q6 alias re-pointing: detection-rule-only in the bounded matrix

**Decision**: Alias re-pointing (CAP-Q6) is represented as a route-change detection **rule**
over observed-versus-resolved model IDs, recorded as an explicit open/gap entry in the
primary bounded matrix (detection-rule-only). Inducing re-pointing requires an
`ANTHROPIC_DEFAULT_<MODEL>_MODEL`-style override that structurally collides with the FR-010
ambient unset-proof (the same run cannot both prove overrides absent and set one). Any
induced re-pointing probe runs as a separate, explicitly-labeled phase with its own
environment and is recorded as labeled inference — never sharing the FR-010 unset-proof run.

The rule itself (reused as the misdelivery record class, R2): when an observed model ID
differs from the resolved qualified ID for a requested route, the treatment is non-scorable
for that route and is recorded separately from resolver fallback — a rule over records, not
new probe machinery (Architecture Notes).

**Rationale**: Verbatim from FR-008 and Assumptions "Alias re-pointing (CAP-Q6)"; resolves
design concept Open Question 4 (detection-rule-only because inducing re-pointing is not
bounded within the FR-010 unset-proof run).

**Alternatives considered**: (a) Induce re-pointing inside the bounded matrix — rejected, it
collides with the unset-proof and inflates the invocation budget; (b) omit CAP-Q6 — rejected,
FR-007 requires every question answered or explicitly marked open.

---

## R12 — Subagent-frontmatter dispatch mechanism (CAP-Q5)

**Decision**: The FR-009 subagent surface uses exactly one fixed mechanism: a file-based
agent definition at `.claude/agents/<probe-name>.md` (YAML frontmatter naming the
unavailable dated model ID), generated at probe time and **not committed**, invoked by an
explicit `@agent-<probe-name>` mention in a fresh, non-`--bare` `claude -p` prompt (default
`-p` loads project-level agent files). An inline `--agents '<JSON>'` definition is a
documented mechanism but does not satisfy FR-009 (no YAML frontmatter, no repo precedent);
an operator MAY run it additionally as a non-binding corroborating probe. Two reliability
limits are recorded as labeled inference, never certified fact: (a) which documented outcome
path (soft remap via `modelUsage`, hard rejection, silent fallback) this surface takes for a
plain unavailable ID; (b) the equivalence between this project-level unnamespaced
file-agent-plus-mention dispatch and CAP-Q5's transfer target (the plugin-namespaced
production Agent-tool routing) is an inference the snapshot entry must state.

**Rationale**: Verbatim from spec Assumptions "Unavailable-model probe mechanism (CAP-Q5)"
and FR-009. The probe-time agent file is generated and not committed so it never becomes a
shipped agent (constitution I) and never pollutes the plugin agent set.

**Alternatives considered**: (a) `--agents` inline JSON as the required mechanism — rejected,
it carries no YAML frontmatter and has zero precedent among the repo's file-based agents;
(b) commit the probe agent file — rejected, it is a throwaway probe artifact, not a shipped
agent.

---

## R13 — FR-010 interference-surface set and the `inherit` caveat

**Decision**: The unset-proof pins to `--fallback-model`/`fallbackModel`,
`CLAUDE_CODE_SUBAGENT_MODEL`, and `availableModels` (absent — not merely an empty list),
proven from the **actual operator environment** used for the probe run. `enforceAvailableModels`
is inert when `availableModels` is unset, so its value is recorded for audit completeness,
not gated. An isolated `CLAUDE_CONFIG_DIR` MAY be layered in as defense-in-depth but does not
by itself satisfy the proof (its isolation is documented as partial). On the subagent surface,
`inherit` equals unset only when the pinned client version is v2.1.196 or later; on an earlier
client `inherit` forces the main-conversation model and is itself a masking risk — the snapshot
records the pinned client version (FR-018) so this is checkable. Organization-level model
restrictions (Claude Enterprise) are entitlement-delivered and cannot be proven absent by local
unset-proof; where the probe account may be subject to them, this is recorded as an explicit
labeled gap, never assumed absent.

**Rationale**: Verbatim from spec Assumptions "Interference-surface set (FR-010)" and FR-010
(`code.claude.com/docs/en/model-config`, `code.claude.com/docs/en/sub-agents`,
`code.claude.com/docs/en/debug-your-config`).

**Alternatives considered**: (a) Rely on `CLAUDE_CONFIG_DIR` isolation as the proof — rejected,
documented as partial (managed settings and exported shell env vars persist);
(b) treat `inherit` as always-equivalent-to-unset — rejected, version-dependent per docs.

---

## R14 — Synthetic-fixture location and unit-layout compliance

**Decision**: The synthetic fixtures live under the purpose-named directory
`tests/speckit-pro/unit/fixtures/claude-telemetry-records/` (files `route-resolution.json`,
`success.json`, `null.json`, `unavailable.json`, `misdelivery.json`). No fixture carries a
top-level `fixture_id` field (the four record-class fixtures are exact-treatment replay
records keyed by `route_resolution_id` such as `CAR-002-RR-FIXTURE-001`; the standalone
route_resolution fixture is keyed by `route_resolution_id`). Test method names are
behavior-named. The new unit test path begins `tests/speckit-pro/unit/`.

**Rationale**: `tests/speckit-pro/unit/test-unit-layout.py` enforces (a) purpose-named
fixture paths with no spec-ID token, (b) `fixture_id` (when present) must equal or prefix
the purpose directory name, (c) behavior-named test methods, and (d) Layer-4 manifest paths
under `tests/speckit-pro/unit/`. The `SPEC_ID_NAME` regex covers `doc|prsg|spec|tacd|xplat`
followed by a digit — `car` is not matched — but the directory is purpose-named regardless,
and omitting `fixture_id` sidesteps the purpose-alignment rule entirely. Deterministic
literal IDs in fixtures satisfy Assumptions "ID conventions" (synthetic fixtures use
deterministic literals).

**Alternatives considered**: (a) Put fixtures under `docs/ai/research/` — rejected, they are
synthetic test data, not evidence, and belong in the unit fixture tree; (b) name the directory
`car-002-...` — rejected, the unit-layout contract forbids spec-ID-named support paths.

---

## R15 — Docs-surface guard (XPLAT-008) allowlist treatment

**Decision**: The three new `docs/ai/research/` deliverables receive the same conscious,
narrow allowlist treatment CAR-001 used: they are added to the `allowed_agent_route_research_exact`
exact-path set in `tests/speckit-pro/unit/test-speckit-pro-runner.py` (schema + snapshot in
WP1's PR; telemetry profile in WP2's PR). They are governed planning/research evidence, not
shipped payload or runtime claims — a repo-only test guard, not a shipped-payload surface.

**Rationale**: The docs-surface guard in `test-speckit-pro-runner.py` iterates changed paths
and requires each `docs/ai/research/**` change to be a conscious allowlist entry (the existing
`allowed_agent_route_research_exact` set already lists the five CAR-001/G56R research files).
Adding the CAR-002 deliverables to that exact set mirrors CAR-001 and keeps the guard narrow
(each entry is a full path, not a prefix). This is the same repo-only test guard treatment the
workflow constraint calls for — not a shipped payload allowance.

**Alternatives considered**: (a) Add a `docs/ai/research/` prefix allow — rejected, too broad;
the guard is intentionally exact-path; (b) leave them unlisted — rejected, the guard fails the
suite on an unlisted `docs/ai/research/**` change.

---

## Technology-choice best practices (Technical Context dependencies)

- **Standard-library JSON Schema validation** — the CAR-001 `validate_manifest` pattern
  (structural walk over `$defs` with `require_exact_keys`/`schema_keys`, explicit `sha256`
  and UTC-timestamp checks) is the proven in-repo approach; reuse it rather than adding
  `jsonschema` (constitution II/VI, FR-016). Load the schema file once, drive required-key
  and `additionalProperties:false` checks from it so the JSON Schema stays the single source
  of truth a reviewer reads (SC-007).
- **`subprocess` for the operator probe** — argument array, `shell=False`, explicit
  return-code handling, an explicit timeout, and `text=True` UTF-8 capture (matches the
  existing `git_diff_changed_paths` pattern in `read_only.py`). The pure logic (matrix build,
  `tuple_id`, sanitization, hashing, fail-closed gating) is separated from the single live
  boundary so tests cover everything except the actual `claude` call (FR-001/FR-002).
- **Deterministic offline test** — validate committed bytes only (fixtures + committed
  snapshot + committed profile); never spawn `claude`; the suite passes with no CLI and no
  network (SC-002; `tests/speckit-pro/AGENTS.md` determinism rule).

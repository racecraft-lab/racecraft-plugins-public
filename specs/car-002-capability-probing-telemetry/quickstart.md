# Quickstart: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

Two audiences, two flows. **Part A** is the operator-only live probe run (the only path
permitted to call the `claude` CLI). **Part B** is the deterministic offline validation that
every contributor and CI runs with zero live model calls. **Part C** is how CAR-003..CAR-011
consume the published contracts.

Paths are repository-relative. Contracts referenced here: [data-model.md](./data-model.md),
[contracts/claude-trace-contract.schema.json](./contracts/claude-trace-contract.schema.json).

---

## Prerequisites

| Flow | Needs |
|------|-------|
| Part A (operator) | The pinned `claude` CLI on `PATH`, valid authentication, Python 3.11+. |
| Part B (everyone) | Python 3.11+ only. **No** `claude` CLI, **no** network. |
| Part C (downstream) | Read access to the committed schema, snapshot, and profile. |

---

## Part A — Operator probe run (operator-only; live)

> This is the single operator-invoked entrypoint permitted to execute live `claude`
> calls (FR-001). It is never run by any test or in CI. Worst-case budget: ~20 live
> invocations (FR-003). If the matrix would exceed the bound, the tool surfaces the
> matrix-definition error before any live call (edge case "Budget overrun").

Entry point: `tests/speckit-pro/layer6-efficiency/lib/claude_capabilities.py` (run as the
operator probe tool). The steps below are what one run performs.

### Step 1 — Confirm raw JSON key spellings (one-shot, before parser is trusted)

Run one `claude -p --output-format json` canary with the fixed canary prompt
`Reply with the single word: ok` and capture raw stdout. Confirm the exact key spellings
the parser depends on — especially the camelCase top-level `modelUsage` (not snake_case
`model_usage`) and its sub-fields `inputTokens`, `outputTokens`, `cacheReadInputTokens`,
`cacheCreationInputTokens`, `contextWindow`, `costUSD`, plus snake_case `usage.*`,
`total_cost_usd`, `num_turns`, `duration_ms`. Any field this confirmation has not run
against is later labeled `observation`, never `fact` (research R3, FR-027).

**Expected**: a JSON payload whose keys match the documented `SDKResultMessage` shape; the
per-model key inside `modelUsage` is the effective model ID (there is no scalar `model`
field). This canary doubles as the CAP-Q1 alias-binding observation for the invoked alias.

### Step 2 — Record authentication mode (and, only in API-key mode, the models endpoint)

Detect the mode from documented signals: `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN`
present ⇒ `api_key`, else `subscription` (FR-014). In `api_key` mode only, call
`GET /v1/models` and store the returned dated IDs and per-model effort flags as
**corroborating** evidence. In `subscription` mode or if unreachable, record the absence as
a gap — never a run failure (research R7; edge case "API models endpoint unreachable").

### Step 3 — Run the bounded, deduped probe matrix (~20 invocations)

Using the fixed canary for every probe (FR-005):

1. **Alias canaries (CAP-Q1..Q4)** — one `claude -p --output-format json` per unique alias
   (`opus`, `sonnet`, `haiku`, `fable`); read the resolved dated model ID from `modelUsage`.
2. **Per-tuple effort acceptance** — one configuration-acceptance check per unique
   (model, effort) tuple. Run in **plain-text `--print`** (which warns naming requested vs
   applied effort) rather than JSON output (which clamps an org effort cap silently), or
   record an explicit no-org-cap assumption. Label acceptance `observation`, never
   certification (research R6). The 6 tuples are `opus__max`, `sonnet__max`, `fable__max`,
   `haiku__max`, `haiku__low`, `sonnet__low`.
3. **Unavailable-model probe, both surfaces (CAP-Q5)** —
   - `print_model`: `claude -p --model <unavailable-id>` with the canary.
   - `subagent_frontmatter`: generate a throwaway (uncommitted) `.claude/agents/<probe>.md`
     whose YAML frontmatter names the same unavailable ID, then invoke it via an explicit
     `@agent-<probe>` mention in a fresh, non-`--bare` `claude -p`. Do **not** pass a
     per-invocation `--model` — that would preempt the frontmatter value under test
     (research R4/R12).
   - For each surface, record `observed_outcome` (soft_remap / hard_rejection /
     silent_fallback / undetermined), the `observed_model_id` from `modelUsage`, and set
     `remap_flagged` when the observed model differs from the requested unavailable ID
     (research R4). Capture the FR-010 `unset_proof` from the **actual** operator
     environment: `--fallback-model`/`fallbackModel`, `CLAUDE_CODE_SUBAGENT_MODEL`, and
     `availableModels` all unset/absent (research R13).
4. **CAP-Q6 (alias re-pointing)** — recorded as a route-change **detection rule**
   (observed ≠ previously-resolved), left `open` in the bounded matrix; inducing re-pointing
   collides with the unset-proof and is a separate labeled phase if run at all (research R11).

### Step 4 — Fail-closed write of the snapshot

For every observation the writer: (a) sanitizes the raw payload to `<home>` before anything
is written; (b) computes the SHA-256 over the exact sanitized UTF-8 bytes and stores the
payload verbatim as a string in `raw_evidence`; (c) validates the observation against the
schema via `claude_trace_schema.py`. Disposition (data-model.md "Snapshot-write dispositions",
FR-023):

- Any schema-invalid or unparseable observation → **abort the whole write**; nothing is
  committed (SC-004).
- An uninterpretable transport failure (non-zero exit with no parseable body, timeout,
  network failure) → **abort the run**; commit nothing; do **not** record "unavailable".
- An interpretable platform observation (unavailable result, endpoint unreachable under
  subscription, a bounded-matrix-unanswerable question) → record as unavailable/gap/open and
  **write** the snapshot.

**Expected output**: one canonical file
`docs/ai/research/claude-runtime-capability-snapshot.json` (replaced in place on re-probe,
`V<n>` bumped; git history preserves priors, FR-011), valid against the
`runtimeCapabilitySnapshot` `$def`, recording alias→dated-ID bindings, one shared evidence
set per tuple, both unavailable-model surfaces, and a `capability_answers` entry for each of
CAP-Q1..Q6 (answered or explicitly open).

### Step 5 — Commit the snapshot and keep the docs-surface guard narrow

Commit the snapshot. Because it is a new `docs/ai/research/**` deliverable, add its exact
path to the `allowed_agent_route_research_exact` set in
`tests/speckit-pro/unit/test-speckit-pro-runner.py` — the same conscious, narrow allowlist
treatment CAR-001 used (a repo-only test guard, not a shipped payload; research R15).

---

## Part B — Deterministic validation (everyone; offline; zero live calls)

Single command:

```bash
python3 tests/speckit-pro/run-all.py
```

**Expected**: the default suite (Layers 1, 4, 5) passes with zero failures on a machine with
**no** `claude` CLI and **no** network (SC-002). The Layer 4 test
`tests/speckit-pro/unit/test-efficiency-claude-telemetry.py` validates, against the schema:

- the four synthetic record-class fixtures (`success`, `null`, `unavailable`, `misdelivery`)
  under `tests/speckit-pro/unit/fixtures/claude-telemetry-records/` (SC-003);
- the standalone `route-resolution.json` fixture (AC-3.1);
- the committed snapshot `docs/ai/research/claude-runtime-capability-snapshot.json`;
- the committed telemetry profile `docs/ai/research/claude-telemetry-capability-profile.json`
  (exactly-one-label per field, nulls preserved — SC-006);

and computes the **37-route → tuple join** from the committed CAR-001 manifest against the
snapshot's `tuple_evidence`, failing closed if any route resolves to zero or to more than one
tuple (SC-005). A fixture or snapshot that drifts from the schema fails the suite and blocks
merge (AC-4.2). No test path spawns `claude` (FR-001/FR-002).

Scoped runs: `python3 tests/speckit-pro/run-all.py --layer 4` (unit only);
`python3 tests/speckit-pro/run-all.py --layer 1` (structural only).

---

## Part C — Downstream consumption (CAR-003..CAR-011 handoff)

A downstream spec binds a treatment **without re-probing** (SC-008):

1. **Resolve the route** — pick a `candidate_route_id` from the CAR-001 manifest; derive its
   `tuple_id` as `<model_selector.requested_value>__<effort_selector.requested_value>`
   (research R1) and read that tuple's shared evidence from the committed snapshot's
   `tuple_evidence`. Mint a `route_resolution` record (schema `routeResolution` `$def`),
   reusing `agent_contract_id`, `candidate_route_id`, and `runtime_capability_snapshot_id`
   verbatim (FR-021). Mint `route_resolution_id` as a non-empty unique string (recommended
   `candidate_route_id` + snapshot ID + timestamp/uuid).
2. **Record the treatment** — wrap that binding in an `exactTreatmentReplay` record (schema
   `exactTreatmentReplay` `$def`) with the observed `record_class`:
   - `success` — fully populated, `scorable: true`.
   - `null` — every nullable field present but null (never dropped), `scorable: true`.
   - `unavailable` — cross-references the snapshot's unavailable observation via
     `runtime_capability_snapshot_id`, `scorable: false`.
   - `misdelivery` — `observed_model_id` ≠ `route_resolution.resolved_dated_model_id`,
     `scorable: false` (route-change detection rule; research R11/R2).
3. **Trust the telemetry classification** — read the telemetry profile to know which fields
   are `stable_native` vs `derived` vs `derived_from_controlled_configuration` vs
   `unavailable` before scoring (SC-006). Reference field values through the profile rather
   than duplicating them.

The four committed synthetic fixtures are the worked examples of step 2. Everything a
downstream consumer needs to reproduce a treatment is in the `exactTreatmentReplay` record;
no capability question CAR-002 owned needs re-answering (SC-008).

**Deferred (non-goals, per spec)**: corpus execution, scoring, statistics, and fallback
ordering are CAR-003 and later — not CAR-002.

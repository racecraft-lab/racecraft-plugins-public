---
topic: "CAR-002 capability probing, telemetry profile, and exact-treatment contract"
slug: "car-002-capability-probing-telemetry"
date: "2026-07-16"
mode: "setup"
spec_id: "CAR-002"
source_input:
  type: "topic"
  ref: "CAR-002 scope section, docs/ai/specs/claude-agent-routing-technical-roadmap.md"
question_count: 8
stop_reason: "natural"
---

# Design Concept: CAR-002 Capability Probing, Telemetry Profile, and Exact-Treatment Contract

> **Source:** CAR-002 scope from `docs/ai/specs/claude-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-16
> **Questions asked:** 8
> **Stop reason:** natural

## Goals

- Freeze the executable candidate set for the pinned Claude Code client by
  capturing a committed `runtime_capability_snapshot` that answers the
  CAR-001 capability questions (CAP-Q1..CAP-Q6) with recorded probe evidence.
- Live probing is operator-only: the probe library ships an operator-invoked
  entrypoint, the operator commits the resulting snapshot, and every repo/CI
  test stays deterministic against synthetic fixtures plus the committed
  snapshot (Q1).
- One canonical snapshot artifact lives at
  `docs/ai/research/claude-runtime-capability-snapshot.json`, beside the
  CAR-001 candidate manifest; re-probes replace it and git history preserves
  priors (Q2).
- The probe matrix dedupes to unique (model, effort) tuples: one canary
  invocation per unique alias for ID binding plus one configuration-acceptance
  check per unique tuple, bounded at roughly 20 invocations worst case; every
  candidate route cites its tuple's shared evidence (Q3).
- The unavailable-model probe covers both surfaces — `claude -p --model
  <unavailable-id>` and a minimal subagent-frontmatter dispatch naming the
  same unavailable ID — recorded separately per surface, with proof that
  `--fallback-model`/`fallbackModel` configuration is unset so the documented
  native fallback chain cannot mask bare platform behavior (Q4).
- The four record contracts (`runtime_capability_snapshot`,
  `telemetry_profile`, `route_resolution`, exact-treatment replay) are
  published as one review-visible JSON Schema with `$defs` under
  `docs/ai/research/`, validated by stdlib-Python logic in
  `claude_trace_schema.py` and a deterministic unit test — the CAR-001
  manifest-schema + parity-validator pattern (Q5).
- Validation is fail-closed at the probe writer (an invalid observation aborts
  the snapshot write) and continuous in CI (the deterministic test validates
  committed synthetic fixtures for all four record classes plus the live
  snapshot) (Q6).
- Committed raw evidence is each probe's complete `--output-format json`
  stdout with home/user paths normalized to `<home>` (existing
  release-readiness sanitization convention) plus a SHA-256 of the sanitized
  payload (Q7).
- **Accepted split — 3 vertical slices** (Q8): (1) snapshot schema + operator
  probe tool + committed snapshot; (2) telemetry profile +
  `route_resolution`/exact-treatment contracts; (3) synthetic replay
  validation across all four record classes. Declared as work packages at
  Plan so PRSG split-PR routing can emit them.

## Non-goals

- No corpus execution, scoring, statistics, or fallback ordering (roadmap
  out-of-scope, reaffirmed throughout the session).
- No payload or guidance changes: shipped agent defaults, prompts, and
  installed caches are untouched.
- No live `claude` invocation in CI or at test time — probing never runs
  outside the operator-only entrypoint (Q1).
- No per-route probing: the 37 candidate routes are not probed individually;
  evidence is recorded per unique (model, effort) tuple (Q3).
- No unsanitized raw payloads in the repository (Q7).
- No Python-only schema definition: the record contracts remain
  platform-neutral JSON Schema artifacts that Codex-side parity work can read
  without executing Python (Q5).

## Design Tree (Q&A log)

### Q1. CAR-002's capability probes execute the real `claude` CLI (`claude -p --model <alias-or-id>`), but the repo's test contract says tests stay deterministic unless explicitly marked live/operator-only. Where should live probing be allowed to run?

**Branch:** Live-probe execution boundary

**Recommended answer:** Operator-only live tool + committed snapshot
> The probe library ships an operator-invoked entrypoint; the operator runs it
> locally and commits a dated snapshot. All repo/CI tests stay deterministic,
> validating schemas against synthetic fixtures and the committed snapshot.
> Grounded in `tests/speckit-pro/AGENTS.md` ("Keep tests deterministic unless
> a test file explicitly marks a live or operator-only path") and the
> roadmap's synthetic-replay-before-live-scoring gate.

**Alternatives offered:**
- CI-gated live probe job: fresher evidence and a reproducible environment,
  but adds API-key secret handling, spend, and nondeterminism to CI.
- Test-time probe with auto-skip: convenient, but results vary by machine and
  it blurs the deterministic/live boundary the suite enforces.

**User's answer:** Operator-only live tool + committed snapshot (Recommended)

---

### Q2. Where should the committed runtime_capability_snapshot artifact live?

**Branch:** Evidence artifact placement

**Recommended answer:** `docs/ai/research/` beside the CAR-001 manifest
> One canonical `claude-runtime-capability-snapshot.json` with internal
> timestamp/probe metadata, next to
> `claude-agent-route-candidate-manifest.json` — re-probes replace it and git
> history preserves priors, mirroring how the manifest itself is versioned.
> Keeps all CAR evidence in one family for the parity validator to extend.

**Alternatives offered:**
- layer6-efficiency fixtures directory: colocates with the consuming runner
  but mixes live evidence into a tree reserved for synthetic test data.
- Dated append-only snapshots directory: explicit history without git
  archaeology, but accumulates stale evidence and forces consumers to resolve
  which snapshot is current.

**User's answer:** docs/ai/research/ beside the CAR-001 manifest (Recommended)

---

### Q3. The 37 candidate routes reduce to 4 unique model aliases (opus, sonnet, haiku, fable) crossed with at most 5 documented effort levels. What should one probe run actually execute?

**Branch:** Probe matrix scope and budget

**Recommended answer:** Dedupe to unique (model, effort) tuples
> One canary invocation per unique alias for ID binding (CAP-Q1–Q4), plus one
> configuration-acceptance check per unique (model, effort) tuple — bounded
> at roughly 20 invocations worst case. Every candidate route cites its
> tuple's shared evidence. Same information as per-route probing at a
> fraction of the spend. Grounded in the CAR-001 manifest's per-alias CAP-Q
> structure and its EFF-1 effort-acceptance note.

**Alternatives offered:**
- Probe all 37 routes individually: strongest per-route provenance but ~2×
  the spend for evidence identical within a tuple.
- Alias bindings only, defer effort acceptance: cheapest now, but CAR-003
  would start scoring on tuples never proven accepted.

**User's answer:** Dedupe to unique (model, effort) tuples (Recommended)

---

### Q4. CAP-Q5 asks what happens when a *subagent's* frontmatter names an unavailable model — but the roadmap's probe verb is `claude -p --model`. Which surface(s) should the unavailable-model probe cover?

**Branch:** Unavailable-model probe surface (CAP-Q5)

**Recommended answer:** Both `-p` and subagent-frontmatter dispatch
> One `-p --model <unavailable-id>` canary plus one minimal subagent dispatch
> whose agent frontmatter names the same unavailable ID, results recorded
> separately per surface. Subagent dispatch is the surface CAP-Q5 actually
> gates (it is how autopilot routes agents). Both probes must prove
> `--fallback-model`/`fallbackModel` configuration is unset: the canonical
> CLI reference (code.claude.com/docs/en/cli-reference, retrieved 2026-07-16)
> documents a native fallback chain — "Enable automatic fallback to the
> specified model(s) when the primary model is overloaded or not available" —
> which would otherwise mask bare platform behavior.

**Alternatives offered:**
- `-p` surface only: simpler harness, but CAR-005's reason-code design stays
  blocked on the exact question this spec exists to pin.
- Subagent dispatch only: loses the nearly-free `-p` comparison point that
  would show whether the two dispatch surfaces behave differently.

**User's answer:** Both -p and subagent-frontmatter dispatch (Recommended)

---

### Q5. CAR-002 defines four record contracts (runtime_capability_snapshot, telemetry_profile, route_resolution, exact-treatment replay). How should these schemas be published?

**Branch:** Schema publication form

**Recommended answer:** JSON Schema file + stdlib validator, CAR-001 style
> One review-visible JSON Schema contract under `docs/ai/research/` with
> `$defs` for the four record types, validated by stdlib-Python logic in
> `claude_trace_schema.py` and a deterministic unit test — exactly the
> manifest-schema + parity-validator pattern CAR-001 shipped
> (`agent-route-candidate-manifest.schema.json` +
> `test-agent-route-research-parity.py`), so Codex-side parity work reads the
> same contract file.

**Alternatives offered:**
- Python-only validators, no JSON Schema file: no duplication to sync, but
  the contract stops being a platform-neutral review artifact.
- Four separate JSON Schema files: maximum modularity, but shared identity
  fields would duplicate across files or need cross-file refs.

**User's answer:** JSON Schema file + stdlib validator, CAR-001 style (Recommended)

---

### Q6. Where should record validation be enforced for the four record classes (success, null, unavailable, misdelivery)?

**Branch:** Validation enforcement point

**Recommended answer:** Fail-closed probe writer + deterministic test
> The operator probe tool validates every record against the schema before
> writing the snapshot — an invalid observation aborts the write, so no
> invalid snapshot can ever be committed. Independently, the unit test
> validates committed synthetic fixtures for all four classes plus the live
> snapshot on every CI run. Matches the parity contract's fail-closed
> evidence rule with defense in depth.

**Alternatives offered:**
- Validate in tests only: simpler tool, but an invalid snapshot can land on a
  branch and the failure surfaces one step removed from the operator.
- Validate in the tool only: leaves committed evidence unguarded against
  later schema drift.

**User's answer:** Fail-closed probe writer + deterministic test (Recommended)

---

### Q7. The snapshot must include 'raw evidence' per probe. CLI JSON output can embed machine-local details (cwd, session paths) that the repo's privacy scan rejects. What form should committed raw evidence take?

**Branch:** Raw-evidence capture and sanitization

**Recommended answer:** Full sanitized payload + SHA-256
> Store each probe's complete `--output-format json` stdout with home/user
> paths normalized to `<home>` (the existing release-readiness sanitization
> convention), plus a SHA-256 of the sanitized payload. Small payloads,
> maximally replayable for the synthetic-replay validation, and passes the
> privacy scan.

**Alternatives offered:**
- Bounded extract + hash, ledger style: consistent with web-evidence
  recording, but probe payloads are small and replay wants whole records.
- Unsanitized full payload: byte-exact fidelity, but committed absolute paths
  fail the privacy scan and leak the operator's machine layout.

**User's answer:** Full sanitized payload + SHA-256 (Recommended)

---

### Q8. The shared size estimator warns: ~860 estimated LOC, suggesting 3 slices — though the roadmap sized CAR-002 at 265 LOC/1 slice and today's setup gate measured 395 reviewable LOC (just under the 400 ceiling). How should CAR-002 be sliced?

**Branch:** Slice sizing

**Recommended answer:** Split into 3 vertical slices
> Estimator-suggested N=3 (`estimate-spec-size` with 4 user stories, 10
> files, 24 FRs → `{estimated_loc: 860, suggested_slices: 3, status: warn}`),
> each slice end-to-end: (1) snapshot schema + operator probe tool +
> committed snapshot; (2) telemetry profile +
> `route_resolution`/exact-treatment contracts; (3) synthetic replay
> validation across all four record classes. Guarantees every PR stays well
> under the review ceiling. The same-day setup gate measured 395 reviewable
> LOC with a primary-surface warning (5 surfaces vs warn threshold 1).

**Alternatives offered:**
- Keep as one spec/slice: trusts the two concrete estimates (roadmap 265,
  setup gate 395-under-ceiling) over the coarse forward guess; the PR-time
  diff-mode gate re-checks with real numbers.
- Split into 2 slices: probing + snapshot end-to-end; telemetry/trace schemas
  + synthetic replay.

**User's answer:** Split into 3 vertical slices (Recommended)

---

## Open Questions

- **What:** The configuration surface for setting reasoning effort on a
  non-interactive `claude -p` invocation (flag, settings file, or environment
  variable) — the effort-acceptance half of the tuple probe depends on it.
  **Why deferred:** Must be pinned from canonical documentation during the
  Specify/research phase; the interview cannot pre-empt the doc evidence.
  **Suggested next step:** Autopilot research records the documented surface
  as a fact; if undocumented, the effort-acceptance probe method is itself
  recorded as a labeled inference/proposed policy, never assumed.
- **What:** Whether the API models endpoint is reachable at probe time
  (API-key vs subscription authentication in the operator environment).
  **Why deferred:** Environment-time fact; the roadmap already scopes the
  endpoint as conditional on API-key authentication.
  **Suggested next step:** The snapshot records the authentication mode of
  every run; the endpoint result is recorded when available and its absence
  is recorded as a gap, not a failure.
- **What:** The exact minimal fixed canary prompt text used by every probe.
  **Why deferred:** Low-stakes content decision; only the invariant matters
  (identical canary across all probes in a snapshot).
  **Suggested next step:** Decide at Plan; record the canary text and its
  hash inside the snapshot.
- **What:** Whether CAP-Q6 (how alias re-pointing manifests) is directly
  probeable inside the tuple matrix or lands only as a route-change detection
  rule over observed vs resolved model IDs.
  **Why deferred:** Depends on whether re-pointing can be induced safely in
  the probe environment; forcing it may not be bounded.
  **Suggested next step:** Specify phase decides: induced probe if bounded,
  otherwise detection-rule-only with CAP-Q6 kept open in the snapshot.
- **What:** Exact file-to-slice assignment for the accepted 3-slice split.
  **Why deferred:** Slice boundaries are declared as work packages at Plan
  (PRSG layer planning) once the concrete file list exists.
  **Suggested next step:** Plan phase declares 3 work packages matching Q8's
  slice seams; PR-time split routing emits them.

## Recommended Next Step

Setup mode — `/speckit-pro:speckit-scaffold-spec CAR-002` is already running:
it writes the workflow file next, enriched from this doc, then hands off to
`/speckit-pro:speckit-autopilot`.

# Phase 0 Research: CAR-001 Candidate Route Baseline and Role Contracts

**Date**: 2026-07-14 | **Branch**: `car-001-candidate-route-baseline`

## Status of unknowns

The spec carries **zero `[NEEDS CLARIFICATION]` markers**, and the Clarify phase
was intentionally skipped for that reason. All nine design branches were walked
in the binding design concept
(`docs/ai/specs/.process/CAR-001-design-concept.md`, Q1–Q9); each is recorded
below in Decision / Rationale / Alternatives form. The only genuinely open items
are **execution-time documentation facts**: the alias-to-resolved-model-ID
bindings and each resolved model's effort-acceptance (`CAP-Q1`–`CAP-Q4`;
available effort levels are model-dependent per `EFF-1`), the undocumented
unavailable-model dispatch behavior (`CAP-Q5`), `fable` resolution and
availability (`CAP-Q4`), and the undocumented execution-time manifestation of
alias re-pointing (`CAP-Q6`). The spec routes each of these to the
capability-question list by construction (FR-008, FR-021, Edge Cases), so they
are not planning unknowns — they are deliverable content the implement phase
records as `CAP-Qn` questions when the docs do not bind them.

## Decisions (from the binding design concept, Q1–Q9)

### D1 — Two artifacts: Markdown record + separate JSON manifest (Q1)

- **Decision**: Ship a human-readable Markdown research record and a separate
  machine-readable JSON manifest, not embedded Markdown tables and not
  JSON-only.
- **Rationale**: Mirrors the repo's established pattern for machine-consumed
  data (`suite-manifest.json`, `speckit-pro-runner.manifest.json`). CAR-002
  binds the manifest to a capability snapshot and CAR-006 materializes from it;
  JSON avoids re-parsing Markdown tables and gives a stable, content-addressable
  artifact. The prose half is load-bearing for AC-1.1/1.2/1.4 (dated, cited,
  labeled).
- **Alternatives considered**: Single Markdown with embedded tables (downstream
  must parse Markdown; versioning semantics fuzzier). JSON-only (loses the dated,
  cited, labeled research prose the ACs demand).

### D2 — Manifest location: `docs/ai/research/` beside the record (Q2)

- **Decision**: Place the JSON manifest next to the record under
  `docs/ai/research/`.
- **Rationale**: Provisional research output, not harness code. Pairing it with
  the record keeps the spike self-contained and reviewable in one place, and
  clearly outside the payload tree (CAR-001 must not change shipped bytes).
- **Alternatives considered**: `tests/speckit-pro/layer6-efficiency/` (lands
  research data in the test tree before any harness exists; harness layout is
  CAR-002/003's decision).

### D3 — Comparator pinned to the latest release tag at research time (Q3)

- **Decision**: Pin the immutable production comparator to `speckit-pro-v2.19.1`
  plus its commit SHA `e343aa2e4ebcb2d48c501f285d7072cfd55722da` (FR-009).
- **Rationale**: The binding Q3 rule is *latest published release tag at
  research time*. Releases are the consumer-installable identity, reproducible
  from the tag forever. Per-agent content hashes make later frontmatter drift
  detectable.
- **Alternatives considered**: `main` HEAD SHA (not what consumers install);
  locally installed cache version 2.18.1 (machine-local, already behind).
- **2.19.0 → 2.19.1 reconciliation (resolved at execution time)**: the design
  concept and scaffold-time spec named `2.19.0` as a parenthetical snapshot taken
  on 2026-07-13. At research time (2026-07-14) the latest published release is
  `speckit-pro-v2.19.1` (`e343aa2e`), a real patch release published later on
  2026-07-13 and descending from 2.19.0. `git diff speckit-pro-v2.19.0
  speckit-pro-v2.19.1 -- speckit-pro/agents speckit-pro/codex-agents` is **empty**
  — the agent and codex-agent files are byte-identical between the two tags (the
  delta touches only runner, skills, dist, docs, scripts, and tests). Pinning to
  2.19.1 is therefore a zero-data-impact refresh: all eleven frontmatter route
  tuples, instruction hashes, and full-file hashes equal their 2.19.0 values.
  spec.md (FR-009, AC scenario 5, and the Assumption) and the plan artifacts are
  reconciled to 2.19.1 accordingly; the implementer records the exact pinned tag
  and SHA in the manifest's `immutable_production_comparator`.

### D4 — Instruction identity: sha256 of the frontmatter-stripped body (Q4)

- **Decision**: Instruction hash = sha256 over the frontmatter-stripped agent
  body; record the full-file sha256 alongside (FR-011).
- **Rationale**: Routes (model/effort) live in frontmatter, so hashing the
  stripped body means a pure route change never invalidates instruction identity
  — the invariant SC-007 verifies. sha256 is the repo convention
  (`speckit-pro-runner.sha256`).
- **Alternatives considered**: whole-file sha256 (a frontmatter-only edit
  spuriously changes the "instruction" hash); normalized-body hash (adds
  normalization policy CAR-003 would have to replicate byte-for-byte — YAGNI).

### D5 — Fact-row evidence: URL + access date + short verbatim quote (Q5)

- **Decision**: Every primary-source fact row carries the official page URL, an
  access date, and a one-to-two-sentence verbatim quote (FR-004).
- **Rationale**: Proves what the docs said at research time even after pages
  change; alias re-pointing (a recorded invalidation trigger) is exactly the
  doc-change class this protects against.
- **Alternatives considered**: URL + date only (no evidence of prior content);
  URL + date + paraphrase (paraphrase drift silently turns facts into
  inferences — the failure AC-1.4 prevents).

### D6 — Candidate universe: four aliases + expected resolved ID, no legacy snapshots (Q6)

- **Decision**: Candidates are the four documented aliases (`opus`, `sonnet`,
  `haiku`, `fable`), each with its expected resolved model ID recorded alongside;
  legacy dated snapshots are not enumerated as separate candidates (FR-012).
- **Rationale**: Shipped frontmatter uses aliases; the route contract is
  "shipped alias + qualified resolved model ID". Alias re-pointing risk is
  handled by invalidation triggers, not by multiplying candidates. Keeps
  CAR-003's screening matrix within budget.
- **Alternatives considered**: also enumerate prior-generation dated IDs
  (roughly doubles the screening matrix; the fallback contract already prefers a
  qualified different-alias route over an unqualified older snapshot).
- **`fable` handling (FR-013, Edge Cases)**: `fable` enters executor-class
  candidate sets and is excluded only by recorded probe or contract evidence,
  never by product-announcement status. Its resolution/availability is a
  capability question.

### D7 — Helper derivation: contract-equivalent translation + mapping table (Q7)

- **Decision**: Derive the `autopilot-fast-helper` contract from
  `speckit-pro/codex-agents/autopilot-fast-helper.toml` as a contract-equivalent
  translation — role prose, bounded jobs, hard rules, output formats carried
  over — accompanied by an explicit platform-field mapping table (FR-017).
  Claude-only fields with no Codex equivalent (e.g. `maxTurns`) carry proposed
  values labeled "proposed SpecKit Pro policy", deferred to CAR-010 (FR-018).
- **Rationale**: AC-1.6 requires the helper's mutation contract in the manifest;
  the parity principle requires both platforms' helpers to be provably the same
  contract with an auditable mapping.
- **Alternatives considered**: port prose only, defer all field mapping (leaves
  the manifest entry incomplete); re-author fresh for Claude idioms (breaks the
  parity audit trail).
- **Mapping hypotheses to verify at execution time**: `sandbox_mode` read-only →
  a comprehensive no-tool `disallowedTools` denylist (the helper's contract is
  prompt-context-only, so it denies reads/web too — stricter than the analysts'
  read-only denylist; proposed policy, deferred to CAR-010); `codex-spark` →
  `haiku` + explicit low effort (starting hypothesis, labeled and probe-gated).

### D8 — Fixture backlog: requirements-level entries only (Q8)

- **Decision**: Each fixture-backlog entry is requirements-level only — the role
  contract to exercise, representative task types, required evidence (tool
  surface, mutation boundary, output format), and a pass/fail signal sketch. No
  full fixture specifications (FR-019).
- **Rationale**: Full fixture specs are CAR-003 Work Package B's job;
  duplicating them here creates drift between two documents (Constitution VI
  single source of truth).
- **Alternatives considered**: full draft fixture specs per agent (written
  before the runner/materializer design exists, they would be partially wrong
  and double the review load).

### D9 — Timebox: one autopilot run; gaps become no-go items (Q9)

- **Decision**: The spike completes in a single autopilot run. Any mandatory
  fact still unverified at the end becomes an explicit no-go item or a stable-ID
  capability question in the go/no-go handoff rather than extending the box
  (FR-023).
- **Rationale**: AC-1.5 already defines the handoff as the completion criterion;
  undocumented behaviors flow to CAR-002 as probe questions by design.
- **Alternatives considered**: fixed wall-clock box with resume (unenforceable
  inside an autopilot run; invites scope creep on a spike whose unknowns flow to
  CAR-002 anyway).

## Research method for the implement phase

These decisions govern *how* the implement phase builds the two deliverables;
the live documentation facts themselves are implement-phase content, not
resolved here.

1. **Fact sourcing (FR-004, FR-006)**: For each platform fact class — model IDs,
   aliases, subagent configuration fields, effort levels, model-resolution
   precedence, plugin-agent field support, fast mode, authentication modes,
   non-interactive telemetry — fetch the current official Anthropic
   documentation page live, capture the source URL, the access date, and a short
   verbatim quote. Only official Anthropic documentation is admissible as a
   platform-fact source. Conflicting claims are rejected or explicitly marked
   unresolved (FR-005); no head-to-head benchmark or native fallback feature is
   claimed where none is documented (FR-007).
2. **Statement classification (FR-006, SC-003)**: Every statement in the record
   is visibly labeled as exactly one of platform fact, reasonable inference,
   proposed SpecKit Pro policy, or unverified assumption. The undocumented
   behavior when frontmatter names an unavailable model is recorded as a
   mandatory probe question, never an assumption (FR-008).
3. **Hash computation (FR-011, FR-025, SC-007)**: Using the Python 3.11+
   standard library only, strip the YAML frontmatter block from each current
   agent `.md`, compute sha256 over the remaining body (instruction identity),
   and compute sha256 over the full file. Record both in the manifest. A pure
   frontmatter route change must leave the instruction sha256 unchanged
   (demonstrable by recomputation).
4. **Surface inventory (FR-003, AC-1.1)**: Enumerate every active source, skill,
   validation, evaluation, generated-payload, and installed-cache surface that
   encodes or consumes agent route policy, so the record's inventory is
   exhaustive. Read-only; nothing is modified.
5. **Capability questions + handoff (FR-021, FR-022)**: Assign stable IDs
   `CAP-Q1…CAP-Qn` in a dedicated section; the go/no-go handoff is the record's
   final section and enumerates the provisional candidate-route manifest, the
   role-contract catalog, the fixture backlog, the telemetry requirements, the
   unresolved capability questions, and the go/no-go decision. It depends on no
   CAR-002 result and claims no candidate is executable before probing.
6. **Validation (SC-006)**: `python3 tests/speckit-pro/run-all.py` must pass
   untouched; the manifest must be valid JSON conforming to the Phase 1 contract;
   a privacy scan confirms no absolute filesystem paths appear in either
   artifact.

## Resolved vs. deferred

- **Resolved at plan time**: artifact shapes and locations (D1, D2), comparator
  identity (D3), instruction-identity contract (D4), evidence style (D5),
  candidate universe (D6), helper-derivation method (D7), fixture-backlog depth
  (D8), timebox and gap policy (D9), the full manifest field set (see
  `data-model.md`), and the machine contract (see
  `contracts/agent-route-candidate-manifest.schema.json`).
- **Deferred by design to the implement phase (recorded, not assumed)**: the
  live alias-to-resolved-model-ID bindings and each resolved model's
  effort-acceptance (`CAP-Q1`–`CAP-Q4`; effort levels are model-dependent per
  `EFF-1`), `fable` resolution/availability (`CAP-Q4`), the undocumented
  unavailable-model dispatch behavior (`CAP-Q5`), and the undocumented
  execution-time manifestation of alias re-pointing (`CAP-Q6`) — each recorded as
  a fact (if the docs bind it) or a `CAP-Qn` capability question (if they do
  not). The helper's proposed `maxTurns` (and any other Claude-only
  subagent-field values) carried as "proposed SpecKit Pro policy", finalized by
  CAR-010.

---
topic: "CAR-001 Candidate Route Baseline and Role Contracts"
slug: "car-001-candidate-route-baseline"
date: "2026-07-13"
mode: "setup"
spec_id: "CAR-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/claude-agent-routing-technical-roadmap.md"
question_count: 9
stop_reason: "natural"
---

# Design Concept: CAR-001 Candidate Route Baseline and Role Contracts

> **Source:** docs/ai/specs/claude-agent-routing-technical-roadmap.md (CAR-001 section) + docs/prd-claude-agent-routing.md (AC-1.1 through AC-1.7)
> **Date:** 2026-07-13
> **Questions asked:** 9
> **Stop reason:** natural (all branches walked; no new critical branches surfaced)

## Goals

- Produce the dated, cited candidate-route and role-contract handoff needed for
  capability probing (CAR-002) without changing shipped defaults.
- Deliver **two research artifacts**: a human-readable Markdown research record
  (`docs/ai/research/claude-agent-route-candidates.md`) plus a separate
  machine-readable JSON `agent_route_candidate_manifest`
  (`docs/ai/research/claude-agent-route-candidate-manifest.json`) that
  CAR-002/CAR-003/CAR-006 bind to programmatically (Q1, Q2).
- Pin the immutable production comparator to the **latest published release tag
  at research time** (speckit-pro 2.19.0) plus its commit SHA, recording the
  eleven current frontmatter tuples with agent content hashes for drift
  detection (Q3).
- Define instruction identity as **sha256 over the frontmatter-stripped agent
  body**, with the full-file sha256 recorded alongside — a pure route change
  (model/effort in frontmatter) never invalidates instruction identity (Q4).
- Build the primary-source fact table with **URL + access date + short verbatim
  quote** per fact row, so the record proves what official docs said at
  research time even after pages change (Q5).
- Identify candidates by the **four documented aliases (opus, sonnet, haiku,
  fable) with expected resolved IDs recorded alongside; no legacy dated
  snapshots as separate candidates** — alias re-pointing risk is handled by
  invalidation triggers (Q6).
- Derive the net-new `autopilot-fast-helper` contract from the Codex helper
  toml as a **contract-equivalent translation with an explicit platform-field
  mapping table**; Claude-only fields (e.g. small `maxTurns`) get proposed
  values labeled "proposed SpecKit Pro policy" per AC-1.4, finalized by
  CAR-010 (Q7).
- Deliver the fixture backlog as **requirements-level entries only**
  (role contract, representative tasks, required evidence, pass/fail sketch
  per agent) — full fixture specs are CAR-003 Work Package B's job (Q8).
- Timebox: **one autopilot run**; mandatory facts still unverified at the end
  become explicit no-go items or open capability questions in the go/no-go
  handoff rather than extending the box (Q9).
- Slice sizing: estimator returned `{estimated_loc: 0, suggested_slices: 1,
  status: ok}` with the spike flag — single slice, no split warranted; sized
  by timebox per the spike escape hatch.

## Non-goals

- No agent frontmatter, prompt, payload, or shipped-default changes (roadmap
  Out of Scope; reinforced by Q2's constraint that nothing lands under
  speckit-pro/'s allowlisted payload dirs).
- No live corpus execution, qualification, or fallback ordering (CAR-003+).
- No legacy dated model snapshots as separate screening candidates (Q6).
- No full draft fixture specs — requirements-level backlog only (Q8).
- No plugin-owned route-policy manifest — that is CAR-006's artifact; this
  spike's JSON manifest is provisional research output (Q2).
- No claim that any candidate is executable before CAR-002 probing (AC-1.5).
- No wall-clock multi-session research program — gaps flow to CAR-002 as
  probe questions instead (Q9).

## Design Tree (Q&A log)

### Q1. Should the agent_route_candidate_manifest be a separate machine-readable JSON file, or embedded as tables inside the Markdown research record?

**Branch:** Artifact shape

**Recommended answer:** Markdown record + separate JSON manifest
> Mirrors the repo's established pattern for machine-consumed data
> (suite-manifest.json, speckit-pro-runner.manifest.json,
> promotion-records.json). CAR-002 binds the manifest to a capability snapshot
> and CAR-006 materializes from it — JSON avoids re-parsing Markdown tables
> and gives a stable content-addressable artifact. Keeps the ~3-file spike
> budget.

**Alternatives offered:**
- Single Markdown record with embedded tables: one fewer artifact, but every
  downstream consumer must parse Markdown tables and "versioned +
  content-addressed" semantics get fuzzier.
- JSON manifest only, minimal prose: maximally machine-friendly, but
  AC-1.1/1.2/1.4 demand a dated, cited research record with visible
  fact/inference/policy labeling — prose is the load-bearing half.

**User's answer:** Markdown record + separate JSON manifest (Recommended)

---

### Q2. Where should the provisional JSON manifest live?

**Branch:** Artifact location

**Recommended answer:** docs/ai/research/, beside the record
> It's provisional research output, not harness code — pairing it with the
> record keeps the spike self-contained, reviewable in one place, and clearly
> outside the payload tree (CAR-001 must not change shipped bytes; anything
> under speckit-pro/'s allowlisted dirs ships). CAR-002 freezes the executable
> subset from it; CAR-006 owns the eventual plugin-owned manifest.

**Alternatives offered:**
- tests/speckit-pro/layer6-efficiency/: puts it where the CAR-002/003 harness
  will consume it, but lands research data in the test tree before any harness
  code exists, and the harness layout is CAR-002/003's design decision.

**User's answer:** docs/ai/research/, beside the record (Recommended)

---

### Q3. Which version identity should pin the immutable production comparator (the eleven current frontmatter tuples)?

**Branch:** Comparator identity

**Recommended answer:** Latest release tag at research time
> Pin speckit-pro's newest published release tag (currently speckit-pro
> 2.19.0) plus its commit SHA. Releases are the consumer-installable identity,
> reproducible from the tag forever; the record also notes the agents/*.md
> content hashes so any later drift is detectable.

**Alternatives offered:**
- main HEAD commit SHA at research time: freshest source, but not what any
  consumer installs and moves daily — weaker "immutable production route"
  anchor.
- Locally installed cache version (2.18.1): reflects a real install but is
  machine-local, already behind the latest release, and not reproducible for
  other operators.

**User's answer:** Latest release tag at research time (Recommended)

---

### Q4. What exactly should the instruction hash cover?

**Branch:** Identity contract

**Recommended answer:** sha256 of the frontmatter-stripped agent body
> Routes (model/effort) live in frontmatter, so hashing the stripped body
> means a pure route change never invalidates instruction identity — exactly
> the invariant the fallback contract expresses ("fallback preserves
> instructions"). Record the full-file sha256 alongside for drift detection.
> sha256 is the repo's existing convention (speckit-pro-runner.sha256).

**Alternatives offered:**
- sha256 of the whole .md file: simpler, but a frontmatter-only route edit
  spuriously changes the "instruction" hash, conflating route identity with
  instruction identity.
- Normalized-body hash (whitespace-insensitive): tolerates cosmetic edits, but
  the normalization rules become policy CAR-003's materializer must replicate
  byte-for-byte — added surface with no current need (constitution VI: YAGNI).

**User's answer:** sha256 of frontmatter-stripped body (Recommended)

---

### Q5. What evidence should each primary-source fact-table row carry?

**Branch:** Evidence style

**Recommended answer:** URL + access date + short verbatim quote
> Each fact row cites the official page, access date, and a one-to-two-sentence
> verbatim excerpt. When docs later change, the record still proves what was
> documented at research time — this is what makes it "dated and cited" rather
> than trust-me. Alias re-pointing (a known invalidation trigger) is exactly
> the kind of doc change this protects against.

**Alternatives offered:**
- URL + access date only: lighter, but when a page changes there is no
  evidence of what it said; disputed facts force re-research.
- URL + date + paraphrase: readable, but paraphrase drift is how documented
  facts quietly become inferences — the failure AC-1.4's separation prevents.

**User's answer:** URL + access date + short verbatim quote (Recommended)

---

### Q6. Should candidates be identified by the four documented aliases with expected resolved IDs, or should older dated snapshots also enter as separate candidates?

**Branch:** Candidate universe

**Recommended answer:** Aliases + expected resolved ID; no legacy snapshots
> Shipped frontmatter uses aliases today, and the route contract is "shipped
> alias + qualified resolved model ID" — each candidate is an alias with its
> documented current resolution recorded beside it. Alias re-pointing risk is
> handled by recorded invalidation triggers, not by multiplying candidates.
> Keeps CAR-003's screening matrix within the PRD's campaign budgets.

**Alternatives offered:**
- Also enumerate prior-generation dated IDs: deeper fallback pool, but roughly
  doubles the screening matrix, and the fallback contract already prefers a
  qualified different-alias route over an unqualified older snapshot.

**User's answer:** Aliases + expected resolved ID; no legacy snapshots (Recommended)

---

### Q7. How literal should the autopilot-fast-helper contract derivation from the Codex toml be?

**Branch:** Helper parity

**Recommended answer:** Contract-equivalent translation + explicit platform-field mapping table
> Carry the role prose, four bounded jobs, hard rules, and output formats over
> verbatim; map platform fields explicitly (sandbox_mode read-only → the
> shared read-only disallowedTools denylist; codex-spark → haiku + explicit
> low effort as the starting hypothesis). Claude-only fields with no Codex
> equivalent (e.g. the small maxTurns value) get proposed values labeled
> "proposed SpecKit Pro policy" per AC-1.4 — CAR-010 finalizes them.

**Alternatives offered:**
- Port prose only, defer all field mapping to CAR-010: smaller spike, but
  AC-1.6 requires the helper's mutation contract in the manifest — deferring
  leaves the entry incomplete.
- Re-author fresh for Claude idioms: breaks the parity principle's audit
  trail — both platforms' helpers must be provably the same contract.

**User's answer:** Contract-equivalent + explicit mapping table (Recommended)

---

### Q8. How detailed should each fixture-backlog entry be?

**Branch:** Fixture backlog depth

**Recommended answer:** Requirements-level entries only
> Per agent: the role contract the fixture must exercise, representative task
> types, required evidence (tool surface, mutation boundary, output format),
> and a pass/fail signal sketch — roughly a half-page per agent. Full fixture
> specs are CAR-003 Work Package B's job; duplicating them here creates drift
> risk between two documents (constitution VI: single source of truth).

**Alternatives offered:**
- Full draft fixture specs per agent: CAR-003 could start faster, but ten
  detailed specs written before the runner/materializer design exists will be
  partially wrong and must be re-reviewed — doubling review load.

**User's answer:** Requirements-level entries only (Recommended)

---

### Q9. What timebox should the workflow record, and what happens if mandatory facts are still unverified when it expires?

**Branch:** Slice sizing (spike timebox)

**Recommended answer:** One autopilot run; gaps become no-go items
> The spike completes in a single autopilot execution of the workflow file.
> Any mandatory fact still unverified at the end lands in the go/no-go handoff
> as an explicit no-go item or open capability question rather than extending
> the box — AC-1.5 already defines the handoff as the completion criterion,
> and undocumented behaviors are supposed to flow to CAR-002 as probe
> questions anyway. Estimator advisory: `{estimated_loc: 0,
> suggested_slices: 1, status: ok}` (spike flag) — no split warranted.

**Alternatives offered:**
- Fixed wall-clock box (e.g. 2 days) with resume: allows multi-session
  research, but wall-clock boxes are unenforceable inside an autopilot run and
  invite scope creep on a spike whose unknowns flow to CAR-002 by design.

**User's answer:** One autopilot run; gaps become no-go items (Recommended)

---

## Open Questions

- **What:** Expected resolved model IDs for the four aliases must be verified
  against official Anthropic docs at execution time; if the docs do not bind
  a Claude Code alias to a dated model ID, the binding becomes a mandatory
  CAR-002 probe question rather than a recorded fact.
  **Why deferred:** Resolvable only during the spike's own doc research —
  interview cannot pre-empt it.
  **Suggested next step:** The autopilot's research phase records it in the
  fact table (fact) or capability-question list (probe question), whichever
  the docs support.
- **What:** The helper's proposed `maxTurns` value (and any other Claude-only
  subagent-field values with no Codex equivalent).
  **Why deferred:** CAR-001 records them as labeled "proposed SpecKit Pro
  policy" per Q7; CAR-010 finalizes with qualification evidence.
  **Suggested next step:** Carry the proposed values in the manifest's helper
  entry; CAR-010 confirms or revises.
- **What:** Whether `fable` resolves in the pinned benchmark environment
  (PRD OQ-4) and the undocumented unavailable-model behavior (hard error vs
  silent substitution).
  **Why deferred:** Environment-time availability facts — AC-1.4 mandates
  recording these as probe questions, never assuming them.
  **Suggested next step:** Enter both as ID'd capability questions in the
  go/no-go handoff for CAR-002's probe design.
- **What:** Capability-question ID scheme and go/no-go handoff form.
  **Why deferred:** Low-stakes formatting decision made by recommendation
  without a dedicated question: numbered stable IDs (CAP-Q1…CAP-Qn) in a
  dedicated section of the research record, with the go/no-go handoff as the
  record's final section (keeps the ~3-file budget from Q1/Q2).
  **Suggested next step:** Autopilot applies this convention during Specify.

## Recommended Next Step

Setup mode — scaffolding continues automatically:
`/speckit-pro:speckit-scaffold-spec CAR-001` populates the workflow file from
this doc, then `/speckit-pro:speckit-autopilot` executes it. (Informational
only; setup has already happened.)

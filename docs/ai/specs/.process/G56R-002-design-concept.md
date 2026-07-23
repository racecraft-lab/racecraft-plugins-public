---
topic: "Capability Discovery, Telemetry Profile, and Exact-Treatment Contract"
slug: "g56r-002-capability-discovery-telemetry"
date: "2026-07-16"
mode: "setup"
spec_id: "G56R-002"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 10
stop_reason: "natural"
---

# Design Concept: Capability Discovery, Telemetry Profile, and Exact-Treatment Contract

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-07-16
> **Questions asked:** 10
> **Stop reason:** natural

## Goals

- Freeze a source-bound executable model/effort candidate set before G56R-003
  performs outcome-bearing evaluation.
- Bind the tested Codex build to an auditable surface matrix covering app-server,
  CLI, and interactive picker evidence (Q1).
- Publish a versioned capability snapshot, telemetry profile, route-resolution
  contract, and exact-treatment trace schema without fabricating unavailable
  fields (Q5–Q6).
- Validate success, null, unavailable-field, misdelivery, and approved or
  unapproved service-reroute records through deterministic synthetic replay
  (Q7).
- Keep every exclusion tuple-local so one unsupported or contradictory candidate
  does not erase valid evidence for unrelated candidates (Q10).

## Non-goals

- Corpus execution, scoring, statistical qualification, candidate ranking, or
  fallback ordering — retained from the roadmap boundary.
- Agent installation, default changes, route-policy materialization, or generated
  payload changes — retained from the roadmap boundary.
- Treating hidden discovery, runtime probing, repository state, or picker
  visibility as authority for an undocumented platform fact (Q2, Q4).
- Committing raw live app-server, CLI, or picker responses (Q7).
- Creating a cross-vendor probing framework or migrating existing Claude/CAR
  probing mechanics (Q8).
- Splitting G56R-002 before the planning gate proves that the guarded slice is
  no longer reviewable (Q9).

## Design Tree (Q&A log)

### Q1. Which runtime boundary should G56R-002 treat as authoritative for capability discovery and telemetry?

**Branch:** Runtime authority and surface coverage

**Recommended answer:** Pinned App Server (Recommended)
> The roadmap and current official Codex documentation expose field-level
> discovery and reroute contracts through app-server, so one pinned protocol
> surface offered the narrowest evidence boundary and smallest implementation.

**Alternatives offered:**
- Surface Matrix: Require app-server, CLI, and interactive picker behavior to agree in this spec.
- Protocol Only: Specify the protocol contract without binding it to a tested Codex build.

**User's answer:** Surface Matrix

---

### Q2. How should hidden or non-picker models discovered through `model/list` affect the executable candidate set?

**Branch:** Candidate eligibility

**Recommended answer:** Record, Exclude (Recommended)
> Hidden entries are useful runtime evidence, but the G56R evidence-authority
> contract permits only the official-source ledger to admit a candidate.

**Alternatives offered:**
- Visible Only: Ignore hidden entries and freeze only models visible in the interactive picker.
- All Eligible: Treat every discovered model as executable regardless of picker visibility.

**User's answer:** Record, Exclude (Recommended)

---

### Q3. How should the scaffold handle the invalidated OSL6 claim?

**Branch:** Source invalidation

**Recommended answer:** Invalidate Claim Only (Recommended)
> The roadmap's source contract is claim-scoped: a changed locator invalidates
> the bound fact, not unrelated discovery evidence. Post-interview repository
> verification showed that OSL6 is historical and the current v3 ledger uses
> broader `OPENAI-DOC-008`, so the old marker's absence alone does not prove a
> current-ledger invalidation.

**Alternatives offered:**
- Block Entire Spec: Stop G56R-002 until every official source-ledger entry is refreshed and re-approved.
- Defer Refresh: Keep the stale claim provisionally and resolve it during implementation.

**User's answer:** Invalidate Claim Only (Recommended)

**Record correction:** Apply this answer to any current `OPENAI-DOC-*` claim
that execution-time revalidation proves changed. Do not amend or consume the
historical OSL6 row as the current ledger.

---

### Q4. If documented discovery is unavailable, what bounded availability probe may G56R-002 use?

**Branch:** Discovery fallback

**Recommended answer:** One Canary Each (Recommended)
> One bounded, non-scored invocation preserves the roadmap's narrow availability
> escape hatch without turning probing into undocumented discovery or
> qualification.

**Alternatives offered:**
- Fail Closed: Do not probe; mark the candidate snapshot unavailable until documented discovery returns.
- Probe Full Matrix: Exercise every candidate repeatedly to infer availability and stability.

**User's answer:** One Canary Each (Recommended)

---

### Q5. What minimum evidence should qualify an exact model-and-effort treatment as executable?

**Branch:** Exact-treatment proof

**Recommended answer:** Profiled Proof (Recommended)
> PRD AC-2.4 permits an approved configured-route proof when the telemetry
> profile supports it, but requested configuration alone cannot prove an
> undocumented effective value. Reroute monitoring closes that evidence gap.

**Alternatives offered:**
- Runtime Only: Require direct runtime observation of the effective model and effort for every tuple.
- Config Is Enough: Treat the requested configuration alone as proof of effective treatment.

**User's answer:** Profiled Proof (Recommended)

---

### Q6. How should missing effective-treatment or reroute evidence affect a candidate tuple?

**Branch:** Unknown treatment state

**Recommended answer:** Exclude as Unknown (Recommended)
> Roadmap OQ-3 and OQ-4 require preserved nulls and classify missing reroute
> observations as unknown rather than proof that no reroute occurred.

**Alternatives offered:**
- Block Snapshot: Fail the entire candidate snapshot if any admitted tuple lacks complete evidence.
- Assume Requested: Assume the requested model and effort ran when no reroute was observed.

**User's answer:** Exclude as Unknown (Recommended)

---

### Q7. What evidence may be committed for capability snapshots and synthetic replay?

**Branch:** Evidence retention

**Recommended answer:** Redacted Fixtures (Recommended)
> Sanitized deterministic fixtures preserve reviewable record shapes and replay
> coverage without retaining environment details or potentially sensitive live
> payloads.

**Alternatives offered:**
- Hashes Only: Commit schemas and hashes but no representative response fixtures.
- Raw Responses: Commit complete live responses so every discovery result can be replayed exactly.

**User's answer:** Redacted Fixtures (Recommended)

---

### Q8. How should the production contract be divided within the roadmap's three-file budget?

**Branch:** Artifact ownership

**Recommended answer:** Adapter Plus Schema (Recommended)
> Isolating Codex protocol behavior from vendor-neutral evidence schemas follows
> the existing parity contract while avoiding a speculative cross-vendor
> framework under the constitution's KISS and YAGNI rules.

**Alternatives offered:**
- Single Module: Keep collection, normalization, schemas, and orchestration in one implementation file.
- Shared Prober Now: Create a cross-vendor probing abstraction and migrate existing vendor logic in this spec.

**User's answer:** Adapter Plus Schema (Recommended)

---

### Q9. The heuristic estimates 297 reviewable LOC against a 265-LOC roadmap target; how should the scaffold slice the work?

**Branch:** Reviewability

**Recommended answer:** One Guarded Slice (Recommended)
> The authoritative estimator returned one suggested slice and the roadmap has
> three naturally ordered increments. Re-running the gate during planning keeps
> the budget binding without prematurely creating a second spec.

**Alternatives offered:**
- Split Two Specs: Separate capability discovery from telemetry and trace contracts now.
- Raise Budget: Keep one slice and revise the roadmap budget upward before planning.

**User's answer:** One Guarded Slice (Recommended)

---

### Q10. If app-server, CLI, and picker evidence disagree for a candidate tuple, what should happen?

**Branch:** Surface disagreement

**Recommended answer:** Exclude Tuple (Recommended)
> A mismatch is evidence about one model/effort tuple. Tuple-local exclusion
> remains fail-closed while preserving independently valid candidates in the
> same versioned snapshot.

**Alternatives offered:**
- Block All: Fail the entire executable candidate freeze until every surface agrees.
- App Server Wins: Use app-server output as authoritative and retain other surfaces only as diagnostics.

**User's answer:** Exclude Tuple (Recommended)

## Grounded Context

- Current documented app-server discovery method:
  [`model/list`](https://learn.chatgpt.com/docs/app-server#list-models-modellist)
  and `modelProvider/capabilities/read` in the app-server API.
- Current documented reroute event:
  [`model/rerouted`](https://learn.chatgpt.com/docs/app-server#turn-events).
- Direct GPT-5.6 prompting guide:
  <https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6.md>.
  It is authority only for API-surface prompt treatment, not Codex custom-agent
  fields, availability, defaults, telemetry, or exact treatment.
- G56R-001 candidate report:
  `docs/ai/research/codex-agent-route-candidates.md`.
- G56R-001 current machine ledger:
  `docs/ai/research/codex-agent-route-candidate-manifest.json`. G56R-002 must
  consume its 22 `OPENAI-DOC-*` records; the report's `OSL-*` rows are
  historical evidence only.
- Shared parity contract:
  `docs/ai/specs/agent-routing-parity-contract.md`.
- Shared candidate manifest schema:
  `docs/ai/research/agent-route-candidate-manifest.schema.json`.

Capability path: current Codex app-server contract and surface behavior ->
official OpenAI documentation plus Context7 library
`/websites/developers_openai_codex` -> repository roadmap and G56R-001 handoff.
Confidence is high for the documented app-server fields and conditional reroute
event, and deliberately unresolved for any CLI or picker field without a direct
documented contract.

## Open Questions

- **What:** Which exact CLI and interactive-picker observations are deterministic
  and automatable for the pinned build without treating UI state as platform
  authority?
  **Why deferred:** Q1 selected the surface matrix, but the roadmap does not
  prescribe the two secondary-surface extraction methods.
  **Suggested next step:** Resolve field and method details during the first
  `$speckit-clarify` session.
- **What:** What normalization key joins app-server, CLI, and picker evidence
  when model labels or visibility differ?
  **Why deferred:** This depends on the actual pinned-build response shapes.
  **Suggested next step:** Record the key and mismatch semantics in `research.md`
  and `data-model.md` during planning.
- **What:** Which telemetry fields have field-level official support on each
  pinned surface?
  **Why deferred:** Q5 fixed the proof rule, while field classifications require
  an execution-time source refresh.
  **Suggested next step:** Build the telemetry profile in Clarify and Planning;
  preserve unsupported fields as `conditional`, `unavailable`, or
  `undocumented`.
- **What:** Which of the 22 current `OPENAI-DOC-*` source records remain valid
  at G56R-002 execution time?
  **Why deferred:** Scaffold spot-checks covered the app-server contract and a
  subset of source families, not the complete v3 consumption ledger.
  **Suggested next step:** Revalidate all current manifest sources before
  freezing candidates and record claim-scoped invalidations without rewriting
  historical `OSL-*` evidence.
- **What:** What exact timeout, output cap, error taxonomy, and transient-failure
  rule govern the one-canary fallback?
  **Why deferred:** Q4 chose the bounded shape but intentionally left numeric
  limits to the reviewed plan.
  **Suggested next step:** Freeze the limits before implementation and include
  them in deterministic tests.
- **What:** Where does the local raw-evidence retention boundary live, and how
  are committed fixture hashes derived?
  **Why deferred:** Q7 chose the Git boundary, while the project-specific local
  retention path and sanitization procedure require plan-level file ownership.
  **Suggested next step:** Document the process in `research.md` and
  `quickstart.md`; never make raw evidence a repository-test prerequisite.

## Recommended Next Step

**Run setup.** This setup-mode interview is already being consumed by
`$speckit-pro:speckit-scaffold-spec G56R-002`. After the scaffold branch is
pushed, start a new Codex task rooted at its dedicated worktree and run
`$speckit-autopilot docs/ai/specs/.process/G56R-002-workflow.md`.

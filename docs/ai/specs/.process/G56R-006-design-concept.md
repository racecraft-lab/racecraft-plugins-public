---
topic: "G56R-006 Capability-aware Resolver, Materializer, Installer, and Strict Override"
slug: "g56r-006-resolver-materializer-installer-strict-override"
date: "2026-08-24"
mode: "setup"
spec_id: "G56R-006"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md"
question_count: 14
stop_reason: "natural"
---

# Design Concept: G56R-006 Capability-aware Resolver, Materializer, Installer, and Strict Override

> **Source:** `docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md`
> **Date:** 2026-08-24
> **Questions asked:** 14
> **Stop reason:** natural
> **Blind-spot pass:** ran — 5 findings surfaced, 2 set aside

## Goals

- Treat `artifact-author`, `sweep-analyst`, and `sweep-classifier` as required
  core agents. The current destination roster is therefore 12 required agents
  plus the optional `autopilot-fast-helper` (Q1).
- Keep the bundled source inventory strict at all 13 TOML files. Apply helper
  optionality only to the installed destination, and only through a qualified
  no-helper path (Q2).
- Extend the canonical G56R-003 materializer so it renders the selected explicit
  model-and-effort route from the original source bytes, preserves the original
  source binding, and proves every non-route field unchanged (Q3).
- Add one injectable runner-owned observation adapter that captures a fresh
  runtime capability snapshot once per install and uses the bounded
  official-ledger availability probe only when discovery is unavailable (Q4,
  Q12).
- Return the capability snapshot and ordered per-agent
  `route_resolution_id`/`resolved_agent_policy_id` records in a top-level
  structured routing block. Keep low-level mutation records mechanical and do
  not create a separate report file (Q5).
- Preserve the current static installer behavior when no route-policy manifest
  is supplied. Activate the new capability-aware path only through an explicit,
  trusted manifest input until a later integration spec changes the default
  (Q6, Q7).
- Apply the explicit global model override to required agents and to the helper
  when a compatible helper tuple exists. If the helper override is
  incompatible, the validated no-helper path wins; required-agent installation
  continues without silently falling back to a different helper route (Q8).
- Remove an existing optional-helper file only when trusted provenance or a
  known rendered-byte match proves plugin ownership. Otherwise preserve it and
  return manual-remediation evidence (Q9).
- Resolve, materialize, and verify the complete batch before disk mutation,
  then apply one rollback-backed sequence that restores prior bytes and modes
  if any write or managed removal fails (Q10).
- When any required agent has no safe route, finish the bounded read-only
  resolution pass for all required agents, return every attempt, and perform
  zero writes (Q11).
- Complete G56R-006 with deterministic injected discovery/probe fixtures and
  fake-home state proofs. Defer live route UAT and real-user-home mutation to
  G56R-011 (Q13).
- Keep G56R-006 as a framework slice: exercise the current complete roster but
  qualify no production routes here. Flag the downstream roadmap's older
  11-agent cohort as reconciliation work required before final composition
  (Q14).
- Keep one thin vertical slice. The shared estimator used four user stories,
  ten files, eighteen functional-requirement groups, and a modifying change;
  it returned `estimated_loc: 385`, `suggested_slices: 1`, and `status: ok`.

## Non-goals

- Final preferred/fallback route selection, final route aggregates, or route
  qualification for any named agent (Q14).
- Weakening the bundled-source completeness check to make the optional helper
  physically absent from the plugin bundle (Q2).
- Treating rewritten destination bytes as original source bytes, retaining the
  legacy regex-only identity proof, or allowing non-route policy fields to
  drift (Q3).
- Passing fixture booleans directly into production resolution without a
  runtime-observation boundary (Q4).
- Writing a route report artifact into the destination or overloading mutation
  operation metadata with policy evidence (Q5).
- Inferring qualified route policies from bundled TOML defaults or requiring
  not-yet-authored final cohort policies for today's static install path (Q6,
  Q7).
- Allowing an incompatible required-agent override to fall back, letting an
  optional-helper miss fail the required batch, or silently selecting another
  helper route after an override miss (Q8).
- Deleting a user-modified same-named helper by filename alone, swapping the
  complete user agents directory, or accepting partial per-file installation
  (Q9, Q10).
- Short-circuiting at the first failed required agent and hiding other bounded
  resolution failures (Q11).
- Per-agent runtime snapshots, stale cached snapshots, live model calls in CI,
  operator-home writes, plugin version changes, or release integration (Q12,
  Q13).
- Expanding this spec into the downstream cohort-routing work merely to repair
  the roadmap's roster-count drift (Q14).

## Design Tree (Q&A log)

### Q1. How should G56R-006 classify `artifact-author`, `sweep-analyst`, and `sweep-classifier` in the destination roster?

**Branch:** Agent roster authority

**Recommended answer:** Required core
> The active installer requires all three and current tests assert a 13-file
> bundle. Treating the three as required preserves shipped behavior and yields
> 12 required agents plus the optional fast helper.

**Alternatives offered:**
- Conditional agents: install them only when their owning workflows are
  enabled, adding policy states and conditional completeness rules.
- Stale inventory: exclude them and remove their installer entries,
  intentionally shrinking current shipped functionality.

**User's answer:** Required core (Recommended)

---

### Q2. Where should the optional fast-helper rule apply?

**Branch:** Source integrity versus destination optionality

**Recommended answer:** Destination only
> Keep the 13-file plugin source bundle strict so packaging drift still fails
> closed. Conditional helper state belongs in destination planning after route
> resolution, not in source validation.

**Alternatives offered:**
- Source and destination: permit the bundled source itself to omit the helper,
  weakening bundle-integrity checks.
- Always install helper: preserve current destination completeness and defer the
  roadmap's no-helper path.

**User's answer:** Destination only (Recommended)

---

### Q3. How should the selected model-and-effort route become byte-proven destination TOML?

**Branch:** Materialization identity

**Recommended answer:** Extend materializer
> The current canonical materializer binds exact source bytes. Extending it to
> render the chosen route while retaining the original source binding avoids
> falsely treating rewritten TOML as the source and keeps non-route fields
> provably unchanged.

**Alternatives offered:**
- Render then prove: add a separate renderer before the current materializer,
  risking treatment of rewritten bytes as original source.
- Keep regex rewrite: retain the installer's destination-only substitution
  without a resolved-policy identity proof.

**User's answer:** Extend materializer (Recommended)

---

### Q4. Who should convert current Codex runtime observations into the resolver's model/effort/capability fields?

**Branch:** Production discovery adapter

**Recommended answer:** Runner adapter
> G56R-005 is a deterministic simulator, so production installation needs an
> explicit adapter rather than fixture booleans. One injectable runner-owned
> adapter keeps observation authority and test seams at the installed-runtime
> boundary.

**Alternatives offered:**
- Caller snapshot: require every caller to supply a fresh validated snapshot,
  shifting freshness and probe responsibility outside the installer.
- Simulator fields: pass fixture-style booleans directly into production
  resolution without a runtime-observation boundary.

**User's answer:** Runner adapter (Recommended)

---

### Q5. Where should route identities, attempts, and rejection reasons be returned?

**Branch:** Resolution evidence contract

**Recommended answer:** Structured response
> Add a top-level routing block containing the batch snapshot and ordered
> per-agent records. This keeps the response inspectable and deterministic
> without adding another destination write or coupling policy decisions to file
> operations.

**Alternatives offered:**
- Separate report file: persist a report during installation, adding another
  atomic write and lifecycle contract.
- Mutation metadata: attach routing evidence to each file operation, coupling
  policy decisions to low-level writes.

**User's answer:** Structured response (Recommended)

---

### Q6. How should G56R-006 coexist with today's static installer before final cohort policies exist?

**Branch:** Backward-compatible activation

**Recommended answer:** Explicit route mode
> Preserve today's static behavior when no policy input is present. A validated
> route-policy manifest explicitly activates the new framework until G56R-011
> owns final composition and installed integration.

**Alternatives offered:**
- Require policies now: remove the static path before downstream cohorts have
  produced final policies.
- Infer policies: turn bundled TOMLs into provisional policies, blurring
  installed defaults with qualification evidence.

**User's answer:** Explicit route mode (Recommended)

---

### Q7. What should activate route-aware installation and supply its candidate policies?

**Branch:** Policy input and provenance

**Recommended answer:** Manifest path
> One trusted, versioned, schema-validated manifest gives the batch a closed
> roster, stable provenance, and one completeness check. Fixture policies can
> exercise the exact same contract.

**Alternatives offered:**
- Inline JSON: accept a full policy object in the runner request, widening the
  public input and provenance surface.
- Per-agent inputs: pass separate fallback fields per agent, making completeness
  and identity joins harder to validate atomically.

**User's answer:** Manifest path (Recommended)

---

### Q8. Should the strict global model override apply to the optional fast helper as well as required agents?

**Branch:** Strict override scope and optional-helper conflict

**Recommended answer:** Required only
> The roadmap names a strict override for required agents while separately
> preserving a no-helper route. Applying it only to the required roster is the
> simplest conflict-free interpretation.

**Alternatives offered:**
- Include helper: evaluate the helper under the explicit override as well.
- Preference only: permit fallback after an override miss, contradicting the
  strict-override contract.

**User's answer:** Include helper

**Notes:** A follow-up resolved the conflict: apply the override to the helper
when a qualified matching tuple exists, but let the validated no-helper path win
when it does not. Required-agent installation must not fail because the helper
is optional.

---

### Q9. When the no-helper path is selected, when may the installer remove an existing helper file?

**Branch:** Managed-file ownership

**Recommended answer:** Proven managed
> Removal is more destructive than omission. Require trusted install provenance
> or a known rendered-byte match before deleting; otherwise preserve the file
> and surface bounded manual remediation.

**Alternatives offered:**
- Name match: delete any same-named file, risking removal of a user-modified
  agent.
- Never remove: omit new writes but always leave a stale helper installed,
  weakening the no-helper proof.

**User's answer:** Proven managed (Recommended)

---

### Q10. What transaction boundary should cover required-agent writes and optional-helper removal?

**Branch:** Atomic installation and rollback

**Recommended answer:** Plan then rollback
> Resolve and verify the full batch before touching disk, then use the existing
> rollback-oriented installer pattern for one bounded apply sequence. A whole
> directory swap is unsafe because the destination also contains unrelated
> user-owned agents.

**Alternatives offered:**
- Swap directory: replace the complete agents directory atomically, endangering
  unrelated files.
- Per-file commits: write each agent independently and allow a partial install
  if a later operation fails.

**User's answer:** Plan then rollback (Recommended)

---

### Q11. If one required agent has no safe route, should resolution continue for the remaining required agents before returning?

**Branch:** Batch failure diagnostics

**Recommended answer:** Resolve all
> Complete the bounded read-only pass for every required agent so one failed run
> reports the whole incompatibility set. The mutation plan remains empty unless
> every required agent resolves safely.

**Alternatives offered:**
- Stop first failure: return sooner but hide failures that would appear on the
  next retry.
- Resolve on demand: require follow-up runs for complete diagnostics,
  complicating reproducibility.

**User's answer:** Resolve all (Recommended)

---

### Q12. How should runtime capability freshness be scoped across one installation batch?

**Branch:** Snapshot consistency

**Recommended answer:** One batch snapshot
> Capture once at invocation start and bind every per-agent resolution to the
> same snapshot ID. Per-agent recapture could make one atomic decision depend on
> mutually inconsistent availability states.

**Alternatives offered:**
- Per-agent snapshots: recapture for each agent and allow mid-batch drift.
- Cached snapshot: reuse an earlier capture until expiry, weakening the fresh
  snapshot requirement.

**User's answer:** One batch snapshot (Recommended)

---

### Q13. What live evidence should G56R-006 require before the framework slice is complete?

**Branch:** Acceptance evidence boundary

**Recommended answer:** Deterministic only
> Inject discovery/probe outcomes and use fake homes for all state tests. Live
> route UAT and real-user-home effects belong to G56R-011's final integration
> boundary.

**Alternatives offered:**
- Operator smoke: require an explicitly authorized live discovery and temporary
  installed-agent smoke in addition to deterministic tests.
- Real home install: make a live user-home mutation part of G56R-006
  acceptance.

**User's answer:** Deterministic only (Recommended)

---

### Q14. How should G56R-006 handle the mismatch between today's 12 required agents and the downstream roadmap's older 11-agent final cohort?

**Branch:** Cross-spec roster drift

**Recommended answer:** Framework plus flag
> Exercise the current complete roster in framework fixtures without qualifying
> routes here. Record the downstream cohort mismatch as required roadmap
> reconciliation before final composition rather than expanding this slice.

**Alternatives offered:**
- Expand this spec: add route qualification for missing roles to G56R-006,
  crossing into downstream cohort scope.
- Use old cohort: ignore the current required roster and constrain the framework
  to the older 11-agent plan.

**User's answer:** Framework plus flag (Recommended)

## Decisions

| Decision | Outcome | Source |
|---|---|---|
| Required roster | 12 current required agents; fast helper optional | Q1 |
| Source completeness | All 13 bundled TOMLs remain mandatory | Q2 |
| Helper optionality | Destination planning only, behind qualified no-helper policy | Q2 |
| Materialization | Extend canonical materializer to render and prove the selected route | Q3 |
| Runtime discovery | One injectable runner-owned adapter | Q4 |
| Evidence output | Top-level structured routing response | Q5 |
| Activation | Explicit policy manifest enables route-aware mode; static mode remains compatible | Q6-Q7 |
| Global override | Required agents are strict; matching helper override installs, incompatible helper uses no-helper | Q8 |
| Managed removal | Provenance or known-byte proof required | Q9 |
| Atomicity | Complete plan first, rollback-backed batch apply | Q10 |
| Failure diagnostics | Resolve all required agents, return all attempts, zero writes on any required miss | Q11 |
| Snapshot | One fresh batch snapshot | Q12 |
| Live boundary | Deterministic fixtures and fake homes only | Q13 |
| Downstream drift | Flag roster reconciliation; do not expand this framework slice | Q14 |
| Sizing | One vertical slice; advisory estimate 385 LOC, status ok | Estimator |

## Open Questions

- The downstream G56R-007 through G56R-011 roadmap still describes an older
  11-agent final cohort while the active installer now has 12 required agents
  and one optional helper. Before final composition, the roadmap must decide
  how `artifact-author`, `sweep-analyst`, `sweep-classifier`, and the proposed
  `consensus-synthesizer`/`gate-validator` roles map into qualification cohorts.
- G56R-011 still owns live route UAT, final route aggregates, default activation
  of route-aware installation, and any real installed-runtime evidence.

## Recommended Next Step

Continue scaffold by populating the G56R-006 workflow and spec-level MOC from
this record, then start the planning stage in the dedicated G56R-006 worktree.

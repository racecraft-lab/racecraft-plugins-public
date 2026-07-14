---
topic: "Candidate Route Baseline and Role Contracts"
slug: "g56r-001-candidate-route-baseline"
date: "2026-07-14"
mode: "setup"
spec_id: "G56R-001"
source_input:
  type: "file"
  ref: "docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md#g56r-001-candidate-route-baseline-and-role-contracts"
question_count: 23
stop_reason: "natural"
---

# Design Concept: Candidate Route Baseline and Role Contracts

> **Source:** docs/ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md, G56R-001
> **Date:** 2026-07-14
> **Questions asked:** 23
> **Stop reason:** natural

## Goals

- Publish a dated, cited Markdown research narrative and a separate machine-readable JSON agent_route_candidate_manifest.
- Cover all twelve named agents with an immutable production route or recorded absence, a semantic role contract, and every evidence-supported candidate model-and-effort route.
- Use current official OpenAI documentation exclusively for platform facts while using repository files for project facts; keep tracked source, cached source, and sanitized installed-state observations separate.
- Use agent-centric records with readable stable IDs plus canonical instruction and contract hashes.
- Finish within one working day with an objective go/no-go packet for G56R-002, including provenance, a per-agent fixture backlog, telemetry needs, and classified unknowns.
- Preserve G56R-001 as one research-only spike; runtime probing, scored qualification, and production mutation remain downstream work.

## Non-goals

- Runtime capability probes, live corpus execution, scoring, qualification, or final fallback ordering (Q12, Q13).
- Agent TOML, installer, prompt, payload, cache, installed-agent, route-default, or version changes (Q22).
- A reusable schema package, validator framework, or new runtime dependency (Q11).
- Publishing raw home paths, credentials, unrelated configuration, or full machine-local snapshots (Q20).
- Removing a project-level candidate solely because it is unavailable on the current machine (Q23).
- Treating local observations as authority for OpenAI platform behavior (Q3-Q5, Q17).

## Slice-sizing Advisory

The shared estimate-spec-size runner received one user story, approximately
three files, seven acceptance-criteria groups, and spike=true. It returned
estimated_loc 0, suggested_slices 1, and status ok. For a research spike this
means LOC sizing is not applicable; the one-working-day timebox is the sizing
control. No split is warranted, and the accepted delivery remains one spike.

## Design Tree (Q&A log)

### Q1. How should G56R-001 package its cited research record and candidate-route manifest?

**Branch:** Artifact contract

**Recommended answer:** Markdown + JSON
> PRD AC-1.5 and AC-1.6 require both a dated research record and a versioned manifest, while Constitution Principle VI prefers structured JSON manipulation.

**Alternatives offered:**
- Markdown only: Simpler to author, but downstream work must recover structured records from prose.
- JSON only: Machine-readable, but weakens the cited narrative and evidence-classification record.

**User's answer:** Markdown + JSON (Recommended)

---

### Q2. What breadth should the provisional manifest use for candidate model-and-effort routes?

**Branch:** Candidate breadth

**Recommended answer:** All eligible routes
> The roadmap assigns executable filtering to G56R-002 and outcome qualification to later specs, so G56R-001 should not pre-filter challengers without evidence.

**Alternatives offered:**
- Curated shortlist: Reduces research volume but may exclude challengers before capability or outcome evidence exists.
- Hypotheses only: Captures guesses without the complete catalog required for downstream freezing.

**User's answer:** All eligible routes (Recommended)

---

### Q3. Which evidence should G56R-001 use to resolve route, configuration, and capability claims?

**Branch:** Evidence hierarchy

**Recommended answer:** Docs + local inventory
> Official sources are needed for platform facts, while PRD AC-1.1, AC-1.3, and AC-1.7 require project source, route, and fixture inventory.

**Alternatives offered:**
- Official docs only: Maximizes platform-source authority but cannot establish repository-specific facts.
- Include executable probes: Could answer runtime questions earlier but crosses the G56R-002 and G56R-003 boundary.

**User's answer:** Official docs only

**Notes:** Q4 and Q5 clarified how this choice applies to project facts.

---

### Q4. Should “official docs only” apply to platform claims while local files remain valid evidence for repository-specific inventory and current production routes?

**Branch:** Evidence authority

**Recommended answer:** Split authority
> This keeps OpenAI platform facts authoritative while allowing the accepted roadmap's repository inventory to be completed from tracked project evidence.

**Alternatives offered:**
- Strict docs only: Rejects local evidence and forces a no-go on the project-inventory acceptance criteria.
- Docs with corroboration: Lets local observations corroborate platform claims but blurs environment evidence with platform authority.

**User's answer:** Strict docs only

**Notes:** Q5 surfaced the resulting acceptance-criteria conflict.

---

### Q5. Strict docs-only evidence cannot establish the repository inventory, production routes, or fixture gaps required by AC-1.1, AC-1.3, and AC-1.7; how should the scaffold handle that conflict?

**Branch:** Acceptance-criteria consistency

**Recommended answer:** Allow project evidence
> Repository files are authoritative for project-only facts without weakening the user's official-docs-only rule for external platform claims.

**Alternatives offered:**
- Accept a no-go handoff: Preserves strict docs-only evidence but deliberately leaves required project inventory unresolved.
- Revise roadmap first: Stops the scaffold so the PRD and roadmap can remove the local-inventory requirements.

**User's answer:** Allow project evidence (Recommended)

**Notes:** This is the final authority decision. Official OpenAI documentation is exclusive for platform facts; repository evidence is allowed only for project facts. It supersedes the stricter interpretation in Q3 and Q4.

---

### Q6. How should the research record handle CLI, desktop/app, app-server, and non-interactive Codex behavior?

**Branch:** Client and surface boundaries

**Recommended answer:** Separate surface records
> PRD AC-1.2 names distinct Codex surfaces, and separate records prevent a capability or telemetry claim from being generalized across clients.

**Alternatives offered:**
- One unified record: Shorter, but hides unsupported surface differences.
- CLI as baseline: Simpler, but leaves desktop, app-server, and non-interactive coverage incomplete.

**User's answer:** Separate surface records (Recommended)

---

### Q7. How should plugin source, cached plugin content, and installed Codex agent files relate in the baseline?

**Branch:** Production and environment state

**Recommended answer:** Record separately
> Tracked plugin source is the immutable production input; cache and installed files are environment evidence that may reveal drift but must not redefine the source contract.

**Alternatives offered:**
- Source only: Deterministic, but cannot report observed installation drift.
- Installed state wins: Reflects one machine but lets local drift redefine production policy.

**User's answer:** Record separately (Recommended)

---

### Q8. How should G56R-001 define Codex contracts for consensus-synthesizer and gate-validator, which currently exist only as Claude agents?

**Branch:** Cross-runtime parity

**Recommended answer:** Semantic parity
> The roadmap requires two parity additions while preserving role, safety, mutation, tool, and output behavior, not Claude-specific configuration syntax.

**Alternatives offered:**
- Literal translation: Copies configuration shape but may confuse Claude mechanics with the intended contract.
- Defer both roles: Avoids mapping uncertainty but leaves the twelve-agent catalog incomplete.

**User's answer:** Semantic parity (Recommended)

---

### Q9. How should agent contracts and provisional candidate routes be identified across the Markdown and JSON artifacts?

**Branch:** Identity and change detection

**Recommended answer:** Readable IDs + hashes
> Readable IDs support review and cross-document references; canonical hashes bind each ID to the exact instruction and contract content required by AC-1.6.

**Alternatives offered:**
- Hashes only: Precise for drift detection but difficult for humans to review.
- Readable IDs only: Easy to scan but cannot prove that referenced content stayed unchanged.

**User's answer:** Readable IDs + hashes (Recommended)

---

### Q10. When should G56R-001 include prompt or context variants alongside model-and-effort candidates?

**Branch:** Prompt and context scope

**Recommended answer:** Only evidence-justified variants
> The PRD permits bounded tuning only for measured overhead hypotheses and retains an unchanged-prompt attribution control.

**Alternatives offered:**
- Model and effort only: Smaller candidate space but omits justified prompt or context candidates.
- Broad prompt exploration: Expands the spike beyond its bounded, evidence-driven scope.

**User's answer:** Only evidence-justified variants (Recommended)

---

### Q11. Which verification depth should the research spike use for its Markdown narrative and JSON manifest?

**Branch:** Artifact validation

**Recommended answer:** Focused artifact checks
> Small Python standard-library checks satisfy deterministic parsing and agreement needs without violating Constitution Principle VI or creating speculative infrastructure.

**Alternatives offered:**
- Manual review only: Minimizes implementation but leaves completeness and agreement dependent on inspection.
- Reusable validator framework: Adds durable tooling but exceeds this one-day research spike.

**User's answer:** Focused artifact checks (Recommended)

---

### Q12. What should G56R-001 say about preferred routes and fallback ordering before qualification exists?

**Branch:** Policy boundary

**Recommended answer:** Hypotheses, no final order
> The roadmap permits starting hypotheses but reserves evidence-backed preferred routes and ordered fallbacks for later qualification and integration specs.

**Alternatives offered:**
- Provisional ordered list: Useful as a starting point but risks presenting unqualified preference as policy.
- No preference signals: Avoids ranking but discards useful roadmap hypotheses.

**User's answer:** Hypotheses, no final order (Recommended)

---

### Q13. How should the spike handle questions that official docs and project inventory cannot resolve?

**Branch:** Unknowns and dependencies

**Recommended answer:** Classify and hand off
> Answerable documentation and inventory questions belong in this spike; executable capability questions belong to G56R-002 and scored questions belong to G56R-003.

**Alternatives offered:**
- Probe until resolved: Crosses the no-runtime-probing and no-scored-execution boundary.
- Leave all open: Protects time but weakens the go/no-go packet by deferring answerable work.

**User's answer:** Classify and hand off (Recommended)

---

### Q14. What should determine the G56R-002 go/no-go handoff at the end of this spike?

**Branch:** Success criteria

**Recommended answer:** Objective completeness gate
> PRD AC-1.5 defines a concrete handoff packet, so completion should be reproducible rather than based on an informal confidence judgment.

**Alternatives offered:**
- Maintainer judgment: Pragmatic, but difficult to reproduce or audit.
- Always hand off go: Maintains momentum but passes unresolved contract or evidence gaps downstream.

**User's answer:** Objective completeness gate (Recommended)

---

### Q15. How should the one-working-day research timebox interact with the objective completeness gate?

**Branch:** Timebox and terminal state

**Recommended answer:** Stop at one day
> A SPIDR Spike is sized by timebox. At the boundary it should emit either a complete go packet or a precise no-go rather than silently expanding.

**Alternatives offered:**
- Extend until complete: Maximizes completeness but makes scope elastic.
- Reduce deliverables: Preserves time only by changing accepted PRD requirements.

**User's answer:** Stop at one day (Recommended)

---

### Q16. How should a candidate be treated when available evidence shows it cannot preserve a named agent’s safety, grounding, mutation, tool, or output contract?

**Branch:** Safety and eligibility

**Recommended answer:** Exclude the candidate
> The roadmap defines these as hard contracts. A known incompatibility is an eligibility failure, not a prompt-tuning opportunity.

**Alternatives offered:**
- Keep but flag it: Retains breadth but admits a known-incompatible route.
- Compensate in prompts: Changes the frozen treatment and may weaken authorization boundaries.

**User's answer:** Exclude the candidate (Recommended)

---

### Q17. How should the research record handle conflicting official documentation or mismatches between documentation and project observations?

**Branch:** Evidence conflicts

**Recommended answer:** Record and leave unresolved
> AC-1.2 requires conflicting claims to be rejected or explicitly unresolved; surface, version, and locator context must be retained instead of inventing a synthesis.

**Alternatives offered:**
- Newest source wins: Simple, but may ignore surface-specific applicability.
- Observed behavior wins: Reflects one environment but lets local state override platform authority.

**User's answer:** Record and leave unresolved (Recommended)

---

### Q18. What level of fixture detail should G56R-001 provide for the three current and nine missing role fixtures?

**Branch:** Evaluation handoff

**Recommended answer:** Per-agent fixture contracts
> AC-1.3 and AC-1.7 require a fixture backlog. Representative tasks, expected behavior, and hard-contract assertions give G56R-003 an actionable handoff without implementing tests now.

**Alternatives offered:**
- Missing-name list: Faster, but gives later qualification little design guidance.
- Implement all fixtures: Closes the gap but exceeds research-only scope.

**User's answer:** Per-agent fixture contracts (Recommended)

---

### Q19. What top-level structure should the JSON candidate manifest use?

**Branch:** Manifest data model

**Recommended answer:** Agent-centric records
> One flat record per named agent keeps its contract, production route, candidates, provenance, and invalidation rules together and follows the constitution's explicit-over-clever guidance.

**Alternatives offered:**
- Normalized tables: Reduces repetition but adds cross-record joins and schema complexity.
- Route-centric records: Simplifies model comparison but fragments the named-agent contract.

**User's answer:** Agent-centric records (Recommended)

---

### Q20. How much machine-local installed-state evidence may the public research artifacts retain?

**Branch:** Sensitive local evidence

**Recommended answer:** Sanitized facts and hashes
> Relevant route fields and checksums can support drift analysis without exposing home paths, credentials, or unrelated local configuration.

**Alternatives offered:**
- Full raw snapshots: Reproducible, but risks publishing machine-specific or sensitive content.
- Omit installed evidence: Safe, but prevents the selected source-versus-installed comparison.

**User's answer:** Sanitized facts and hashes (Recommended)

---

### Q21. What provenance should each official platform claim carry so later specs can detect staleness?

**Branch:** Freshness and invalidation

**Recommended answer:** URL + date + applicability
> Exact source locators, retrieval dates, Codex surfaces, and documented client or feature applicability make later invalidation checks possible.

**Alternatives offered:**
- URL only: Concise, but weak for freshness and surface boundaries.
- Copy source snapshots: Preserves a point in time but duplicates external documentation and creates maintenance risk.

**User's answer:** URL + date + applicability (Recommended)

---

### Q22. If the inventory uncovers a stale agent definition, installer defect, or payload mismatch, should G56R-001 fix it?

**Branch:** Scope cuts and mutation

**Recommended answer:** Record only, do not fix
> Fixing a discovered defect would mutate the baseline under study and mix production work into a research-only spike.

**Alternatives offered:**
- Fix critical defects: Reduces immediate risk but crosses the accepted mutation boundary.
- Fix every defect: Makes the spike open-ended and absorbs downstream work.

**User's answer:** Record only, do not fix (Recommended)

---

### Q23. Should a candidate’s absence from this machine remove it from the project-level candidate manifest?

**Branch:** Eligibility versus availability

**Recommended answer:** Keep eligibility separate
> AC-1.6 explicitly distinguishes project-level candidate eligibility from installation-time availability, which G56R-002 later binds to a capability snapshot.

**Alternatives offered:**
- Exclude unavailable locally: Produces a runnable local set but confuses one installation with project eligibility.
- Ignore availability entirely: Preserves breadth but omits required environment evidence.

**User's answer:** Keep eligibility separate (Recommended)

## Open Questions

- **What:** Which exact model-and-effort tuples are currently documented as eligible for each named role?
  **Why deferred:** The answer must come from current official OpenAI documentation gathered during the research spike, not from scaffold-time assumptions.
  **Suggested next step:** In G56R-001 implementation, enumerate current official sources using the selected capability path and record URL, date, surface, applicability, and conflicts.

- **What:** Which project-level candidates are executable in each target installation and Codex surface?
  **Why deferred:** Executability requires a versioned runtime capability snapshot and exact treatment evidence.
  **Suggested next step:** Resolve in G56R-002 through non-mutating capability discovery and the declared telemetry profile.

- **What:** Which passing route should be preferred and how should qualified fallbacks be ordered?
  **Why deferred:** The answer requires controlled outcome, reliability, and resource evidence that does not exist in this spike.
  **Suggested next step:** Resolve through G56R-003 qualification and the later cohort-policy specs without treating G56R-001 hypotheses as final policy.

## Recommended Next Step

Continue the current G56R-001 scaffold: generate the populated workflow and
SPEC-MOC from this Design Concept, commit and push the setup branch, then start
a new Codex task rooted at this worktree and run $speckit-autopilot with the
workflow path.

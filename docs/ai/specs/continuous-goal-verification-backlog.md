# Continuous Goal Verification Backlog Catalog

**Source of record for all 71 typed-judgment opportunities (JEV-001 through JEV-071).**

This catalog replaces the external handoff bundle. It carries every field a
future spec needs for a deferred item: bind-at surfaces, required evidence,
proposed behavior, authority boundary, evaluation metric, dependencies, and
the disposition this roadmap gave it. It is a reference document read on
demand, not always-on agent context.

**Source PRD:** [../../prd-continuous-goal-verification.md](../../prd-continuous-goal-verification.md)
**Roadmap:** [continuous-goal-verification-technical-roadmap.md](continuous-goal-verification-technical-roadmap.md)
**Derived from:** handoff bundle v2.0, backlog schema 1.1, research dated 2026-09-18 and revised 2026-09-19 (America/Chicago).
**Bundle status at derivation:** `proposal_not_implemented_or_benchmarked`. Nothing here is implemented; every entry is a proposal.

Sources that live in a private repository are withheld from this public
catalog and counted, not named. Where the bundle named that repository in
prose, this catalog says "the delegation runtime."

---

## How to turn a deferred entry into a spec

1. Confirm VRFY-002, VRFY-003, and VRFY-004 are merged; every deferred entry is a consumer of that foundation.
2. Check the entry's **Depends on** list; each dependency must be delivered or explicitly waived.
3. Add a Feature to the PRD with `AC-N.*` criteria derived from **Required evidence**, **Proposed behavior**, **Authority boundary**, and any listed **Acceptance** bullets, then a matching roadmap entry. Allocate the next `VRFY-###` above all historical use.
4. Add one rubric to the shared catalog under its **Primitive**, string-only, pinned to the qualified model version.
5. Ship both host bindings in the same PR. Insert at the **Bind at** surface as an annotation; change no gate result.
6. Record a baseline for the **Measure** metric before enabling anything beyond shadow.

## Cross-cutting design context

### The eight rubric families

Every semantic check reuses one of these judgment families; a new entry is a new consumer, not a new family: relevance; applicability and routing; entailment and fidelity; coverage; equivalence and conflict; scope and weakening; utility and durability; escalation and uncertainty.

### Primitive rules

- **Noul** for one atomic truth probability. No confidence field.
- **Choice** for a closed classification; always include a no-match or insufficient-evidence option. Relative among options.
- **Score** only for a genuinely ordered dimension with descriptive levels. Keep the full distribution; the expectation is not evidence of concentration and must not be interpolated into a number.
- Questions in one batch are independent; a judgment that depends on a prior answer is a later request.
- Question ids carry no meaning to the model; instructions must name the state fields they read.
- Never combine correctness, risk, complexity, and importance in one number. Required-item coverage is conjunctive.

### Operations that stay deterministic

Never ask the model to: count markers; compute cost or LOC; resolve paths; determine git ancestry or merged status; enforce worktree ownership; validate JSON; maintain ids; check hashes or signatures; apply patches; choose permission rules; approve archive deletion; treat tool installation as consent; or replace a successful native test or model check. Preserve the existing distinctions: publication versus generation versus rendered delivery versus human approval versus UAT; current versus stale proof; waiver versus pass; planning completion versus implementation completion.

### Model facts at derivation (2026-09-19)

- Current model `jev-1.13.0`; aliases `jev-latest` and `jev-preview` move on release, so pin the versioned id and record the reported id.
- Budgets: 64k tokens for state plus all questions; 32k for state plus the longest question. Text only.
- Documented weaknesses: literal reading, counting and arithmetic, date comparison, indirection, distractor-heavy state, adversarial state, contradictory instruction and criteria, structural invariants across separate questions, generation. Keep identities, counts, and permissions in code.
- The plugin defaults to the OpenRouter backend, which accepts only string instructions and criteria.

### Source-review dispositions carried from the bundle

| Source idea | Disposition | Entries |
|---|---|---|
| Versioned decision contract and additive journal | adopt as proposal | JEV-056, JEV-057 |
| Historical model comparison | adopt with three distinct replay modes | JEV-058, JEV-053 |
| Immediate full event-sourced storage rewrite | not proposed by note and not added; migration is conditional after evidence | JEV-069, JEV-071 |
| Threshold-only ImplementationAuthorized example | do not adopt; require existing independent authority and per-obligation evidence | JEV-028, JEV-062 |
| MCP described as side-effect free | qualify; no local domain mutation is not absence of data egress or billing | JEV-056 |
| Human choice becomes binding by semantic inference | do not adopt; semantic fidelity is advisory and original human provenance controls | JEV-008, JEV-061 |
| Custom goal verifier after every turn | adopt as change-triggered boundary verification; no claim native hosts expose identical hooks | JEV-061, JEV-062, JEV-063, JEV-064 |
| System One/System Two test-time-compute synergy | conditional evaluation hypothesis; no speed/cost/quality claim transferred | JEV-067, JEV-070 |

### Inherited findings to revalidate before broad reuse

These were observed in the delegation runtime's existing typed-judgment consumers and in this repository at the bundle's pinned revisions. Treat each as open until a spike reclassifies it.

- **Uncertainty handling.** A triage that rounds a Score to an action records confidence but does not let it force review, and discards the distribution. Uncertainty, absent evidence, and partial evidence must override automated keep or discard decisions.
- **Context coverage.** Inspecting a file's first 2,000 characters or a prefix-truncated patch is a visible limitation, not complete evidence. Retrieve the relevant span, process all hunks in bounded units, and track omissions.
- **Budget accounting.** String lengths are not bytes or tokens. Account for actual serialized UTF-8 and both documented token budgets; label any estimate as an estimate.
- **Responsiveness versus completion.** A partially addressing answer can be responsive. That routes work; it does not establish coverage. One judgment per atomic obligation.
- **Skill teaching.** Weighted-mean Score explanations overstate what the number means; merge-readiness examples need explicit incomplete-evidence and no-authority language. Instructions and criteria are versioned, testable assets.
- **Provider adaptation.** Preserve raw output, but do not spread permissive field-name guesses across languages. Share contract fixtures and a discriminated primitive schema.
- **PR closure ordering.** At the pinned revision, the resolve skill posted and resolved before final verification and push, and fetched only the first 100 threads. Semantic closure comes after verification and pushed-SHA confirmation, with full pagination first.

### Implementation defaults

- **enablement:** off until explicit per-project activation
- **first enabled mode:** shadow
- **provider network access:** existing typesafe-mcp only, through a qualified trusted-parent adapter
- **repository and data consent:** required before every outbound request; data classes and provider are explicit
- **live evaluations:** separate authorization; never in ordinary CI
- **authority:** existing parent, human permissions, deterministic gates and ledgers; no new authority from a judgment or journal
- **state storage:** additive decision journal; existing authoritative stores remain authoritative
- **scheduler:** parent-observed meaningful boundaries first; no automatic per-token or every-tool hooks
- **offline replay:** no provider, no worker dispatch, no business side effects
- **missing judgment:** unknown/not_run, never success; preserve existing workflow behavior in optional modes
- **native synthesis:** named consensus-synthesizer on both hosts; parent cannot replace it
- **backlog is not approval:** P1/P2 priority does not enable a check, authorize spend, or authorize implementation of all items
- **shadow qualification:** A true shadow result cannot reach the live orchestrator/worker before decisions are sealed. If the native MCP result is visible, classify it as advisory, not shadow; use offline/post-run replay until an isolated adapter is qualified.

---

## Disposition summary

| Disposition | Count | IDs |
|---|---|---|
| Deferred: P2 in source | 23 | 001, 006, 007, 012, 014, 020, 024, 026, 027, 029, 030, 031, 035, 039, 040, 042, 045, 046, 047, 049, 050, 051, 054 |
| Deferred: P1 single-artifact check | 26 | 002, 003, 004, 008, 009, 010, 011, 013, 015, 016, 017, 018, 019, 021, 022, 025, 028, 032, 033, 034, 036, 037, 041, 043, 044, 052 |
| In scope (see each entry for its VRFY spec) | 13 | 005, 023, 038, 053, 055, 056, 057, 058, 061, 062, 063, 064, 070 |
| Deferred (bundle tranche T4): second-host visibility and cross-repository causality | 3 | 048, 059, 069 |
| Deferred (bundle tranche T5): conditional extension | 6 | 060, 065, 066, 067, 068, 071 |

---

## Entries

### Discovery and evidence

#### JEV-001: Skill intent disambiguation

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice + applicability Nouls
- **Bind at:** Shared capability discovery; all skill entrypoints
- **Required evidence:** Current user request, active interactive/autonomous mode, actual installed skill descriptions and role permissions.
- **Proposed behavior:** Shortlist likely skills, then confirm applicability against their complete contracts; include no-match. Distinguish PRD vs Coach, Grill Me vs scaffold, and status vs execution.
- **Authority boundary:** Explicit invocation wins. Never auto-invoke a disabled-model-invocation or human-only skill, or expand the permitted tool set.
- **Measure:** Wrong-skill rate, unnecessary invocations, and missed correct skills on a labeled routing set.
- **Depends on:** none beyond the shared foundation
- **Sources:** S3, D9

#### JEV-002: Targeted reference retrieval

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul relevance
- **Bind at:** speckit-coach; shared reference library; spec-context-analyst
- **Required evidence:** Task and deterministic shortlist of current reference sections, including source versions.
- **Proposed behavior:** Rank the smallest useful sections instead of loading entire methodology, consensus, or formal-methods documents.
- **Authority boundary:** Mandatory contracts remain loaded. Preserve omitted-candidate counts and local/native fallback.
- **Measure:** Relevant-section recall, context tokens, and task success versus existing retrieval.
- **Depends on:** none beyond the shared foundation
- **Sources:** S13, S3; 1 private delegation-runtime source(s) withheld

#### JEV-003: Code-context reranking

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per candidate
- **Bind at:** codebase-analyst; scaffold blind-spot pass; implementation context
- **Required evidence:** Task plus discovered symbol/path/signature/doc excerpts and current source identity.
- **Proposed behavior:** Add a semantic reading-order shortlist after lexical, ripwire, or other installed code retrieval. Fetch real source before citing behavior.
- **Authority boundary:** Do not rewrite upstream map provenance or use signature relevance as implementation proof.
- **Measure:** Relevant-code recall at the context budget and downstream correction rate.
- **Depends on:** none beyond the shared foundation
- **Sources:** S14, S3; 1 private delegation-runtime source(s) withheld

#### JEV-004: Research-passage filtering and ranking

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul + Choice relation
- **Bind at:** domain-researcher; Plan research; checklist/analyze remediation
- **Required evidence:** Question, retrieved passages, source authority/version/date, and retrieval coverage.
- **Proposed behavior:** Prioritize passages answering the actual question; distinguish supporting, conflicting, and unrelated evidence.
- **Authority boundary:** Jev does not browse, establish freshness, or authenticate sources. Keep material counterevidence.
- **Measure:** Evidence recall and unsupported research claims at equal research cost.
- **Depends on:** none beyond the shared foundation
- **Sources:** D8, D10, S3

#### JEV-005: Claim-to-source support checking

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** In scope: VRFY-007

- **Primitive:** Choice: supports / contradicts / insufficient
- **Bind at:** Shared grounding boundary; all analyst reports; PR and handoff summaries
- **Required evidence:** Exact claim and independently fetched source span with enough surrounding context.
- **Proposed behavior:** Check quote existence in code, then classify the contextual relation. Produce a review queue, not a rewritten answer. Reuse the same support rubric at changed-evidence boundaries; record exact claim/span versions so a later source edit invalidates only affected support judgments.
- **Authority boundary:** Unsupported is not necessarily false; missing context is not contradiction. Never suppress the original finding. Never equate receipt replay with a fresh source read.
- **Measure:** Unsupported-claim detection precision/recall and reviewer overturn rate.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** JEV-056
- **Related:** JEV-056, JEV-057, JEV-063
- **Sources:** D8, S3, A1, X1; 1 private delegation-runtime source(s) withheld

#### JEV-006: Instruction-bearing evidence flags

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul
- **Bind at:** Trusted parent handling external/reviewer-derived reports
- **Required evidence:** Bounded untrusted content already obtained through its authorized source.
- **Proposed behavior:** Flag instructions directed at the reader or attempts to redirect the task; retain the original material for isolated inspection.
- **Authority boundary:** Not a prompt-injection firewall. Preserve the sweep broker isolation and do not grant its workers new tools.
- **Measure:** Attack detection and benign false-positive rates; unchanged permission surface.
- **Depends on:** none beyond the shared foundation
- **Sources:** D7, S3; 1 private delegation-runtime source(s) withheld

### Product discovery and language

#### JEV-007: Interview branch prioritization

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Separate Noul/Score dimensions
- **Bind at:** grill-me
- **Required evidence:** Current design branches, recorded human answers, proposed questions, and project evidence.
- **Proposed behavior:** Rank unanswered consequential decisions; identify questions already answered. The reasoning agent writes and asks the next question.
- **Authority boundary:** No simulated user answers and no Grill Me inside autopilot or subagents. Importance and uncertainty stay separate.
- **Measure:** Consequential decisions resolved per question and avoidable repeated questions.
- **Depends on:** none beyond the shared foundation
- **Sources:** S10, D4

#### JEV-008: Interview-to-record fidelity

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice entailment + Noul
- **Bind at:** Grill Me Design Concept; PRD interview records
- **Required evidence:** Human answer with verified origin, proposed durable wording, and surrounding question.
- **Proposed behavior:** Detect strengthened promises, omitted qualifications, and invented decisions before writing the handoff. Bind interview fidelity to the original human decision event and goal-contract version; retain qualifications across compaction.
- **Authority boundary:** A model label cannot establish human authorship or consent. Parent verifies the original decision. A goal verifier cannot declare a user decision binding.
- **Measure:** Unratified requirements introduced into downstream artifacts.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-061, JEV-068
- **Sources:** S10, S11, S4, A1

#### JEV-009: Atomic and observable acceptance criteria

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per criterion
- **Bind at:** speckit-prd; Specify
- **Required evidence:** One requirement/acceptance criterion and relevant constraints.
- **Proposed behavior:** Flag compound obligations, undefined success measures, ambiguous actors, and outcomes that cannot be observed as written.
- **Authority boundary:** Suggest clarification or decomposition; do not invent business targets or thresholds.
- **Measure:** Acceptance criteria requiring reinterpretation during implementation/UAT.
- **Depends on:** none beyond the shared foundation
- **Sources:** S11, D2

#### JEV-010: Semantic PRD-to-roadmap crosswalk

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul coverage + pairwise equivalence
- **Bind at:** speckit-prd; Coach roadmap workflow
- **Required evidence:** Stable feature/SPEC IDs and bounded matching feature/scope excerpts.
- **Proposed behavior:** Verify that the required 1:1 crosswalk is substantively faithful, not merely that IDs match.
- **Authority boundary:** Code owns cardinality and stable IDs. Candidate matches do not authorize merging or renumbering entries.
- **Measure:** Uncovered or distorted product features and duplicate implementation scope.
- **Depends on:** none beyond the shared foundation
- **Sources:** S11

#### JEV-011: Non-goal and constraint drift

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul + Choice relation
- **Bind at:** PRD; Design Concept; Plan; review boundaries
- **Required evidence:** Ratified non-goal/constraint and the proposed changed requirement or design.
- **Proposed behavior:** Detect new scope and weakened constraints incrementally when artifacts change.
- **Authority boundary:** Never treat repeated agent agreement as user ratification; preserve the source chain.
- **Measure:** Unapproved scope introduced per completed workflow.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4, S11

#### JEV-012: Vertical-slice and dependency critique

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per slice/edge
- **Bind at:** Coach roadmap decomposition; scaffold sizing; O4/O5 planning
- **Required evidence:** Candidate slice, observable outcome, declared interfaces, and proposed dependency edges.
- **Proposed behavior:** Flag horizontal-only slices, hidden prerequisites, and unclear independent value; offer alternative review units.
- **Authority boundary:** Code retains size counts, graph/cycle checks, topology, and thresholds. Jev does not invent approved dependencies.
- **Measure:** Re-slicing after implementation and independently reviewable delivery slices.
- **Depends on:** none beyond the shared foundation
- **Sources:** S13, S14

#### JEV-013: Glossary entity alignment

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice with no-match + Noul
- **Bind at:** ubiquitous-language; advisory identifier lint
- **Required evidence:** New identifier/use context and candidate existing glossary rows.
- **Proposed behavior:** Map synonyms to known terms and suggest a genuinely new term only when no existing definition fits.
- **Authority boundary:** Keep settled definitions, row order, and the existing human confirmation requirement.
- **Measure:** Accepted mappings and reduced duplicate concepts.
- **Depends on:** none beyond the shared foundation
- **Sources:** S12, D11

#### JEV-014: Terminology meaning-drift detection

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice relation
- **Bind at:** Glossary lint; PRD/spec/plan/code consistency
- **Required evidence:** One canonical term and usages from changed artifacts/code.
- **Proposed behavior:** Identify one name used for incompatible concepts or a definition silently changing across layers.
- **Authority boundary:** Do not automatically rename public APIs or overwrite canonical meanings.
- **Measure:** Human-confirmed terminology conflicts per flagged usage.
- **Depends on:** none beyond the shared foundation
- **Sources:** S12

### Scaffold and planning

#### JEV-015: Blind-spot evidence triage

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Support Choice + relevance Noul
- **Bind at:** speckit-scaffold-spec blind-spot pass
- **Required evidence:** Returned analyst finding, current source/history excerpt, scope, and declared dependencies.
- **Proposed behavior:** Prioritize grounded, consequential blind spots before the live interview; retain unresolved evidence requests.
- **Authority boundary:** The mandatory attempt and fail-open/deadline contract remain unchanged. Missing evidence is not a clean pass.
- **Measure:** Useful interview issues found and unsupported blind spots shown to users.
- **Depends on:** none beyond the shared foundation
- **Sources:** S14; 1 private delegation-runtime source(s) withheld

#### JEV-016: Workflow-prompt fidelity

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per ratified obligation
- **Bind at:** speckit-scaffold-spec prompt population
- **Required evidence:** Approved roadmap/design decisions and generated Specify/Clarify/Plan prompt sections.
- **Proposed behavior:** Check that prompts carry actual goals, non-goals, and required dependencies into downstream phases.
- **Authority boundary:** Worktree binding, branch selection, bootstrap consent, and generated zones remain deterministic.
- **Measure:** Approved constraints lost at the scaffold-to-autopilot handoff.
- **Depends on:** none beyond the shared foundation
- **Sources:** S14

#### JEV-017: Marker-free ambiguity detection

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per requirement
- **Bind at:** After Specify, alongside G1
- **Required evidence:** Requirement text, defined terms, actors, and explicit assumptions.
- **Proposed behavior:** Find unresolved choices even when no NEEDS CLARIFICATION marker was written; route findings to existing Clarify handling. Expose newly discovered ambiguity as an obligation-specific advisory during a running phase, not just a marker scan after the phase.
- **Authority boundary:** Do not skip existing marked issues. Begin advisory; any added routing rule requires explicit contract tests. Adding an ambiguity does not rewrite the approved goal contract or reset a phase budget.
- **Measure:** Consequential ambiguities discovered after Plan versus before it.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-061, JEV-062
- **Sources:** S4, X1

#### JEV-018: Semantic clarification closure

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice relation + Noul sufficiency
- **Bind at:** Clarify executor return; parent edits; G2
- **Required evidence:** Original ambiguity, source answer/evidence, and proposed resolution.
- **Proposed behavior:** Detect evasive answers, contradiction, and marker deletion without a real resolution.
- **Authority boundary:** Parent retains edits and provenance classification; Jev cannot manufacture explicit-human provenance.
- **Measure:** False closure and repeated clarification of the same issue.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4

#### JEV-019: Plan-to-requirement coverage

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per obligation
- **Bind at:** Plan/G3; spec-context-analyst
- **Required evidence:** Atomic requirement plus candidate architecture, data-model, interface, and migration excerpts.
- **Proposed behavior:** Construct evidence-backed coverage edges and find obligations with only vague design treatment.
- **Authority boundary:** Artifact existence, schema checks, constitutional checks, and selected formal receipts remain necessary.
- **Measure:** Unplanned obligations discovered during implementation.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4

#### JEV-020: Alternative-design comparability

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Separate Score/Noul dimensions
- **Bind at:** Plan research; Coach architecture advice; artifact decision pages
- **Required evidence:** Actual candidate approaches and the same approved constraints/evidence for each.
- **Proposed behavior:** Identify alternatives compared on different criteria, unsupported advantages, and missing tradeoffs.
- **Authority boundary:** The reasoning agent makes architecture recommendations; no single blended score decides architecture.
- **Measure:** Unsupported design claims and reviewer-requested redesign.
- **Depends on:** none beyond the shared foundation
- **Sources:** S13, S20, D4

#### JEV-021: Checklist-domain applicability

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Independent Noul per domain
- **Bind at:** Coach checklist selection; autopilot Checklist
- **Required evidence:** Spec/plan risk signals and discovered domain descriptions.
- **Proposed behavior:** Select multiple relevant domains and highlight omitted security, migration, privacy, performance, or reliability concerns.
- **Authority boundary:** Mandatory domains stay mandatory; a low probability must not waive a required check.
- **Measure:** Important missed domains and unnecessary checklist work.
- **Depends on:** none beyond the shared foundation
- **Sources:** S13, S4

#### JEV-022: Gap-remediation validation

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul + source relation Choice
- **Bind at:** Checklist G4; Analyze repair loop; Converge boundaries
- **Required evidence:** Original gap, proposed artifact diff, and supporting research/source.
- **Proposed behavior:** Check that the edit addresses the actual gap instead of removing its label or replacing it with an unsupported assertion.
- **Authority boundary:** Use existing serial edits and shared repair reservations; no new retry allowance.
- **Measure:** Gap recurrence and cosmetic closure rate.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4

#### JEV-023: Requirement-to-task semantic coverage

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** In scope: VRFY-005

- **Primitive:** Noul per atomic obligation
- **Bind at:** Tasks/G5; task sidecar production
- **Required evidence:** Requirement and the full candidate task set linked to it, including acceptance conditions.
- **Proposed behavior:** Distinguish a real implementation plan from a task that only repeats an FR identifier; track uncovered sub-obligations. Make coverage a per-obligation projection that can be invalidated and reevaluated after relevant task/plan changes; preserve the source FR and acceptance IDs.
- **Authority boundary:** Code owns ID joins and counts; absent evidence cannot be averaged away by well-covered requirements. Planning coverage is not implementation completion.
- **Measure:** Known missing obligations caught before implementation and false coverage passes.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** JEV-056
- **Related:** JEV-061, JEV-062, JEV-063
- **Sources:** S4, A1, X1

#### JEV-024: Task executable-scope completeness

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per required field/relationship
- **Bind at:** Tasks producer; task_execution sidecar
- **Required evidence:** Task, its accepted inputs/outputs, planned paths, dependencies, and validation intent.
- **Proposed behavior:** Flag underspecified outputs, missing validation intent, or a task too broad for its declared scope.
- **Authority boundary:** Existing schema, ownership, sidecar reconciliation, and path validation remain authoritative.
- **Measure:** Task restarts caused by missing execution context.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4, S19

#### JEV-025: Analyze finding normalization

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice + pairwise equivalence
- **Bind at:** Analyze/G6; consensus intake
- **Required evidence:** Findings with exact requirement links, source evidence, and candidate duplicate pairs.
- **Proposed behavior:** Group equivalent defects; separate behavioral defects from optional style suggestions; flag conflicting findings.
- **Authority boundary:** Retain every finding ID and source. Required LOW/MEDIUM defects are not dismissed by a severity score.
- **Measure:** Duplicate repair effort and required defects misclassified as optional.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4

### Orchestration and execution economics

#### JEV-026: Consensus evidence-domain routing assistance

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Independent Noul per evidence domain
- **Bind at:** Consensus intake; parse-consensus-categories boundary
- **Required evidence:** Unresolved item, its existing category tags, and current evidence gaps.
- **Proposed behavior:** Suggest missing codebase/spec/domain expertise and detect obviously inconsistent tags.
- **Authority boundary:** Do not bypass mandated analyst rounds or override explicit categories without a reviewed routing-contract change.
- **Measure:** Unnecessary analyst calls and missed necessary expertise.
- **Depends on:** none beyond the shared foundation
- **Sources:** S2, S3

#### JEV-027: Substantive agreement and dissent mapping

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Pairwise Choice / Noul
- **Bind at:** Claude consensus-synthesizer; Codex parent synthesis
- **Required evidence:** Analyst proposals, cited evidence, assumptions, and minority objections.
- **Proposed behavior:** Distinguish equivalent wording from real disagreement; show when apparent agreement relies on the same unsupported premise. Provide semantic agreement/dissent annotations to the named synthesizer on both hosts; retain all analyst evidence and original votes.
- **Authority boundary:** Jev is not an extra independent vote; no confidence-based manufacture of consensus. PR #583 requires actual named-synthesizer results on Claude and Codex. Jev and the parent cannot replace this role.
- **Measure:** Suppressed material dissent and repeated consensus rounds.
- **Implementation note:** Consume current agent_inventory.json. Preserve the required named consensus-synthesizer on both native hosts.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-056, JEV-066
- **Sources:** S2, S4, D5, R1, R2, A1

#### JEV-028: Evidence-backed readiness vector

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Independent Nouls/Choices
- **Bind at:** G6.5 confidence-gate companion output
- **Required evidence:** Current coverage, unresolved issues, provenance, and verification availability.
- **Proposed behavior:** Show the weakest evidenced dimensions beside the existing confidence composite, with per-item source links. Display a versioned per-obligation semantic vector alongside the existing five-criterion confidence output and observed deterministic gates.
- **Authority boundary:** Do not silently replace the existing 0.90 composite or average away a required defect; calibrate any future enforcement separately. The architecture note’s 0.95/0.05 example is illustrative, not a production gate; do not emit ImplementationAuthorized from Jev alone.
- **Measure:** Readiness false positives and operator usefulness versus self-rated readiness alone.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-061, JEV-062, JEV-064
- **Sources:** S4, D5, A1, R1

#### JEV-029: Semantic parallelism warnings

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per candidate task pair
- **Bind at:** Phase 7 batching; PR-resolution partitions; task execution control
- **Required evidence:** Deterministically shortlisted task pairs, owned paths, shared state/contracts, and actual task descriptions.
- **Proposed behavior:** Flag cross-file semantic coupling or shared fixtures that path-only partitioning might miss.
- **Authority boundary:** Jev can add a conservative review/serialization warning; it cannot override path conflicts, locks, or dependency order.
- **Measure:** Cross-task collisions and needless serialization.
- **Depends on:** none beyond the shared foundation
- **Sources:** S9, S7

#### JEV-030: Stable repair-family recognition

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Pairwise equivalence Noul/Choice
- **Bind at:** Shared execution-control ledger; recurring review findings
- **Required evidence:** Current failure plus prior repair invariant, attempt, and results.
- **Proposed behavior:** Recognize reworded versions of the same defect so repairs target the same root issue. Attach verifier feedback to frozen invariant/obligation IDs and existing reservation IDs across rewordings, resume, and retries.
- **Authority boundary:** Code owns ledger identity and ceilings. A semantic label never resets or enlarges the repair budget. Unknown ownership stays unresolved; no semantic remapping can create a fresh repair allowance.
- **Measure:** Repeated ineffective repairs and budget-reset attempts.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-061, JEV-066
- **Sources:** S4, S7, A1, X1

#### JEV-031: Bounded escalation advice

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Responsiveness/coverage Nouls + route Choice
- **Bind at:** Main orchestrator; optional delegation-runtime handoff
- **Required evidence:** Task requirements, actual worker result, permitted available workers, and remaining budget.
- **Proposed behavior:** Recommend deeper review or a stronger available worker only for clearly undercovered work, preserving useful partial output. Use current unmet-obligation evidence, not report fluency, as the input to escalation advice; report whether escalation repaired the specific failure in evaluations.
- **Authority boundary:** No automatic cloud redispatch, changed native model/effort, or override of explicit user routing. Consent and spend remain separate. Do not change provider, native subscription model, or effort settings automatically.
- **Measure:** End-to-end quality per native quota/cost and unnecessary escalations.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-062, JEV-067
- **Sources:** S2, S7, X1, D13; 1 private delegation-runtime source(s) withheld

### Implementation and verification

#### JEV-032: Behavioral test-assertion coverage

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per behavior
- **Bind at:** Implement executor; TDD; UAT preparation
- **Required evidence:** Acceptance behavior, exact test body/assertions, and fixture context.
- **Proposed behavior:** Find tests whose names mention a requirement but whose assertions do not exercise it; flag vacuous or unrelated assertions.
- **Authority boundary:** Jev does not run tests or establish coverage. Retain actual red/green, mutation, and integration evidence.
- **Measure:** Requirement-relevant assertions and defects missed by nominally matching tests.
- **Depends on:** none beyond the shared foundation
- **Sources:** S4, S7

#### JEV-033: Phantom implementation screening

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per task outcome
- **Bind at:** Post Verify Implementation and Verify Tasks
- **Required evidence:** Task outcome, current implementation excerpt, artifact paths, and native verification observations.
- **Proposed behavior:** Flag placeholder implementations, disconnected code paths, or documentation presented as completed behavior.
- **Authority boundary:** Structural checks, current source reads, and producing tests remain required; Jev is an additional screening signal.
- **Measure:** False completed-task reports detected before handoff.
- **Depends on:** none beyond the shared foundation
- **Sources:** S7

#### JEV-034: Patch scope and guard-weakening review

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Atomic Nouls + contextual Score
- **Bind at:** Implementation return; review-fix return; final integration review
- **Required evidence:** Approved task/constraints plus all relevant changed hunks, including tests, defaults, and permissions.
- **Proposed behavior:** Annotate scope expansion and weakened checks; aggregate explicit findings without losing per-hunk coverage.
- **Authority boundary:** Never authorize apply/merge. A truncated patch cannot receive an unqualified low-risk verdict.
- **Measure:** Out-of-scope or weakening edits caught; end-of-patch blind spots.
- **Depends on:** none beyond the shared foundation
- **Sources:** S7; 1 private delegation-runtime source(s) withheld

#### JEV-035: Failure-family diagnostic triage

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice with insufficient-evidence option
- **Bind at:** Test/build failure handling; error recovery
- **Required evidence:** Actual logs, baseline result, changed scope, environment identity, and rerun history when available.
- **Proposed behavior:** Prioritize likely environment, assertion, dependency, or unrelated failures to guide bounded investigation.
- **Authority boundary:** Never declare a failure flaky from one observation, skip a failed gate, or rerun outside the shared budget.
- **Measure:** Time to correct diagnosis and incorrectly dismissed regressions.
- **Depends on:** none beyond the shared foundation
- **Sources:** T4, S4

#### JEV-036: Verification-claim reconciliation

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice entailment
- **Bind at:** Post reports; task_results; final handoff
- **Required evidence:** Worker claims plus independently observed command results, snapshots, omissions, and waivers.
- **Proposed behavior:** Flag statements such as all tests passed or feature complete when the cited producer evidence does not establish them. Compare proposed completion claims with current goal-obligation evidence after consumed worker results and before a terminal handoff.
- **Authority boundary:** An agent-authored receipt alone is not proof; keep native producer observations and hash/freshness checks. Delegation-runtime transport completion, task settlement, an agent summary, and goal satisfaction are distinct facts.
- **Measure:** Unsupported completion claims in delivered reports.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-059, JEV-062, JEV-064
- **Sources:** S7, S5, A1, X1

### Review, delivery, and formal artifacts

#### JEV-037: Review feedback routing and cross-file hints

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice + Noul
- **Bind at:** speckit-resolve-pr; trusted review coordinator
- **Required evidence:** All paginated current threads, current source, candidate affected symbols, and thread IDs.
- **Proposed behavior:** Classify code defect/style/question, detect semantic duplicates, and flag hidden cross-file changes before partitioning.
- **Authority boundary:** No thread suppression. Unknown edit scope is reviewed/serialized; parent owns Git and GitHub mutations.
- **Measure:** Review triage time, cross-file races, and lost thread coverage.
- **Depends on:** none beyond the shared foundation
- **Sources:** S9

#### JEV-038: Review-fix closure verification

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** In scope: VRFY-006

- **Primitive:** Noul + Choice entailment
- **Bind at:** Immediately before reply/resolution, after final verification and push confirmation
- **Required evidence:** Original complaint, final changed source, tests, reply, and verified pushed commit SHA.
- **Proposed behavior:** Check that the actual defect was corrected and the reply accurately describes that correction; unsupported false-positive dismissals stay open. Record the original feedback ID, fix snapshot, pushed SHA and remote observation in the closure decision; invalidate after a relevant later edit.
- **Authority boundary:** Do not resolve from a model score alone. Correct current resolve-before-final-verify ordering and fetch all pages first. No reply or resolution replay; side effects remain behind publication confirmation and idempotency checks.
- **Measure:** Reopened review threads and false resolutions.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** JEV-056
- **Related:** JEV-057, JEV-060, JEV-063
- **Sources:** S9, A1; 1 private delegation-runtime source(s) withheld

#### JEV-039: Stack-layer semantic coherence

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per proposed layer/contract
- **Bind at:** Stack manager; reviewability split planning; PR emission
- **Required evidence:** Approved layer descriptions, changed-hunk ownership, interface dependencies, and actual Git graph.
- **Proposed behavior:** Identify layers that mix unrelated concerns or rely on behavior not introduced by their declared predecessors.
- **Authority boundary:** Git determines ancestry; existing packet/topology validation and explicit split decisions control mutations.
- **Measure:** Reviewer-requested stack rework and hidden cross-layer dependencies.
- **Depends on:** none beyond the shared foundation
- **Sources:** S14, S4, S19

#### JEV-040: Formal-methods applicability advice

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per risk; Choice over supported catalog candidates
- **Bind at:** Coach formal-methods guidance; scaffold interview
- **Required evidence:** Behavioral risk, state-transition requirements, simpler available checks, and actual supported checker catalog.
- **Proposed behavior:** Highlight behaviors where a model could add value and suggest a supported modeling/checking approach.
- **Authority boundary:** Only explicit operator selection activates formal checks. No tool installation or second orchestrator.
- **Measure:** Useful model selections versus unnecessary modeling work.
- **Depends on:** none beyond the shared foundation
- **Sources:** S13, S6

#### JEV-041: Formal-property intent and weakening checks

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice relation + atomic Nouls
- **Bind at:** Formal author return; Plan/planning/final/Post reconciliation
- **Required evidence:** Requirement, property contract, actual model changes, assumptions, bounds, and implementation mapping.
- **Proposed behavior:** Flag mismapped properties, strengthened assumptions, or weakened obligations before accepting a modeling change.
- **Authority boundary:** TLC/Apalache/Quint-related native checking and current trace receipts alone establish their respective results; Jev never proves a theorem.
- **Measure:** Human-confirmed model/requirement mismatches and green-by-weakening attempts.
- **Depends on:** none beyond the shared foundation
- **Sources:** S6

#### JEV-042: Artifact-gallery signal detection

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per manifest signal
- **Bind at:** artifact-author selection
- **Required evidence:** Runtime gallery manifest and actual planning record.
- **Proposed behavior:** Assess signals such as competing approaches or brownfield change consistently, then apply manifest routing in code.
- **Authority boundary:** Always-selected entries stay selected. Do not hardcode a stale template list or add prefetching contrary to the per-page contract.
- **Measure:** Missed useful artifact types and unnecessary generated pages.
- **Depends on:** none beyond the shared foundation
- **Sources:** S20

#### JEV-043: Artifact content fidelity

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice support + Noul coverage
- **Bind at:** Artifact author/parent handoff
- **Required evidence:** Generated textual claims and current planning source; observed rendered body text when available.
- **Proposed behavior:** Catch generic filler, invented architecture, and omitted feature-specific obligations even when every FILL slot is populated.
- **Authority boundary:** Jev is text-only and cannot verify layout, successful preview delivery, or human approval. Preserve existing rendering observations.
- **Measure:** Incorrect or generic artifact claims reaching reviewers.
- **Depends on:** none beyond the shared foundation
- **Sources:** S20, S5, D6

#### JEV-044: UAT scenario completeness

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Noul per acceptance condition
- **Bind at:** uat-runbook-author; implementation handoff
- **Required evidence:** Requirements and draft scenarios with setup, actions, observable results, and negative cases.
- **Proposed behavior:** Find acceptance criteria or failure paths not represented by a runnable scenario.
- **Authority boundary:** Coverage of a runbook is not execution, visual verification, or user acceptance.
- **Measure:** Missing acceptance scenarios and late UAT surprises.
- **Depends on:** none beyond the shared foundation
- **Sources:** S5, S7

### Memory and lifecycle

#### JEV-045: Durable lesson triage

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Separate support/utility/durability Nouls
- **Bind at:** Eligible implement/codebase/spec-context memory; retrospective proposals
- **Required evidence:** Proposed lesson and relevant current source span, not merely the head of a named file.
- **Proposed behavior:** Separate true-but-trivial, task-specific, stale, and genuinely reusable lessons; route uncertainty to review.
- **Authority boundary:** Respect the existing scope matrix. Never persist raw reviewer text, transient hypotheses, or notes for memory-ineligible roles.
- **Measure:** Useful retained lessons, stale advice, and incorrect dismissals.
- **Depends on:** none beyond the shared foundation
- **Sources:** S8; 1 private delegation-runtime source(s) withheld

#### JEV-046: Semantic retrieval of approved memory

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul relevance
- **Bind at:** Eligible agents and approved durable project records
- **Required evidence:** Current task and source-verified stored entries with provenance/freshness.
- **Proposed behavior:** Retrieve relevant knowledge when wording differs from file names or old task terms.
- **Authority boundary:** Current source and artifacts override memory. No synthetic Codex parity claim for Claude-specific memory storage.
- **Measure:** Helpful memory retrieval and stale-memory contamination.
- **Depends on:** none beyond the shared foundation
- **Sources:** S8; 1 private delegation-runtime source(s) withheld

#### JEV-047: Archive summary and residual-status checking

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice support + Noul contradiction
- **Bind at:** speckit-archive-cleanup; project memory summaries
- **Required evidence:** Verified merge provenance, shipped artifacts, archived requirements, and status references.
- **Proposed behavior:** Check that the archive summary describes what shipped and detect prose still calling completed work pending.
- **Authority boundary:** Git/runner policy decides merge status, paths, deletion eligibility, and recovery commands. Preserve historical process evidence.
- **Measure:** Misleading archive summaries and stale active-state references.
- **Depends on:** none beyond the shared foundation
- **Sources:** S16

#### JEV-048: Semantic health on the read-only dashboard

**Priority:** P1 | **Kind:** derived_view | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** Deferred (bundle tranche T4): second-host visibility and cross-repository causality; follow-on PRD

- **Primitive:** No new evaluation by default; receipt rendering
- **Bind at:** speckit-status
- **Required evidence:** Existing immutable semantic receipts, current artifact hashes, and actual workflow/gate state.
- **Proposed behavior:** Display uncovered requirements, stale judgments, unresolved evidence, and checks not run separately from workflow progress. Render recorded goal progress, unmet obligations, last relevant evidence change, verifier status, and journal/projection lag without refreshing them.
- **Authority boundary:** No file writes, hidden cache creation, paid calls, or replacement of the deterministic next-spec algorithm. Do not repair journals, advance consumer offsets, update access timestamps, or create caches in status mode.
- **Measure:** Actionable dashboard findings with zero read-only contract violations.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-057, JEV-062, JEV-069
- **Sources:** S15, A1, X1

#### JEV-049: Upgrade customization-intent comparison

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice relation + Noul
- **Bind at:** speckit-upgrade manual merge/restore review
- **Required evidence:** Backed-up customization, upstream change, and proposed restored/merged result.
- **Proposed behavior:** Highlight lost local intent, revived deprecated behavior, or incompatible instructions before the operator approves restoration.
- **Authority boundary:** Backups, hashes, actual CLI results, and operator decisions remain controlling; do not activate deferred migration helpers.
- **Measure:** Lost customizations and post-upgrade behavioral regressions.
- **Depends on:** none beyond the shared foundation
- **Sources:** S18

#### JEV-050: Optional installation diagnostic assistance

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice over documented failure families
- **Bind at:** speckit-install; Codex install adapter; Jev capability health
- **Required evidence:** Non-secret version/platform/capability checks and exact error outputs.
- **Proposed behavior:** Provide targeted documented recovery advice for ambiguous failures; ordinary successful setup needs no model call.
- **Authority boundary:** Lower priority than coverage/review. No automatic install, global config edit, key inspection, or provider switching.
- **Measure:** Useful recovery suggestions without unnecessary calls or environment mutations.
- **Depends on:** none beyond the shared foundation
- **Sources:** S17, T3, T5

#### JEV-051: Task-to-issue and cross-artifact publication fidelity

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Noul per task obligation
- **Bind at:** Installed task-to-issues or equivalent publication capability
- **Required evidence:** Canonical task IDs/requirements and proposed issue descriptions.
- **Proposed behavior:** Check that published work items preserve acceptance conditions, dependencies, and scope after condensation.
- **Authority boundary:** Integrate only through discovered installed capability boundaries; code handles IDs, deduplication, permissions, and GitHub writes.
- **Measure:** Published issues missing actionable requirements.
- **Depends on:** none beyond the shared foundation
- **Sources:** S3, S1

### Maintainer and release quality

#### JEV-052: Skill activation regression evaluation

**Priority:** P1 | **Kind:** evaluation | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P1 single-artifact check; a consumer of VRFY-002 through VRFY-004 that needs its own measured baseline

- **Primitive:** Choice + applicability Nouls in offline/replayed evaluation
- **Bind at:** tests/speckit-pro; skill-description changes
- **Required evidence:** Labeled requests, expected eligible skills, forbidden modes, and both platform payloads.
- **Proposed behavior:** Evaluate ambiguous routing pairs and reject-all cases before shipping changed descriptions; compare native routing with assisted routing.
- **Authority boundary:** Jev is one evaluated candidate, not the gold-label authority. Deterministic packaging tests stay separate.
- **Measure:** Routing accuracy, unnecessary invocation, and forbidden-mode activation.
- **Depends on:** none beyond the shared foundation
- **Sources:** S1, S3, D9

#### JEV-053: Rubric and model-version regression harness

**Priority:** P1 | **Kind:** evaluation | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** In scope: VRFY-002 (harness) and VRFY-012 (corpus and holdout)

- **Primitive:** All primitives; replay plus opt-in live evaluation
- **Bind at:** Shared semantic-check test corpus; typesafe-mcp and delegation-runtime contract fixtures
- **Required evidence:** Human-labeled real failures, counterexamples, provider fixtures, and frozen rubric/model versions.
- **Proposed behavior:** Measure calibration, abstention, coverage, and end-to-end outcomes before changing prompts, thresholds, or model aliases. Separate historical policy replay, counterfactual policy simulation, and separately authorized live model reevaluation; add frozen full-run trajectories for sequential verifier evaluation.
- **Authority boundary:** No paid nondeterministic calls in normal unit tests or secrets exposed to untrusted fork PRs; separate training and holdout cases. Live reevaluation is neither deterministic replay nor permission to repeat historical side effects. Model judgments are not gold labels.
- **Measure:** False-pass/false-block rates, calibration error, and quality at fixed budget.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** JEV-056
- **Related:** JEV-058, JEV-070
- **Sources:** D5, D6, S1, A1, X1, W1

#### JEV-054: Documentation and release-claim fidelity

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Disposition:** Deferred: P2 in source; validate value first

- **Primitive:** Choice entailment
- **Bind at:** Authored docs; release notes; contributor workflow; generated-source review
- **Required evidence:** Authored claims, actual source/manifest/helper status, and observed validation output.
- **Proposed behavior:** Flag claims of supported modes or completed verification not backed by the shipping contract.
- **Authority boundary:** Regenerate dist/docs/hashes mechanically. Never use a semantic verdict instead of release or payload consistency checks.
- **Measure:** Unsupported support claims and shipped documentation drift.
- **Depends on:** none beyond the shared foundation
- **Sources:** S1, S19, T3

#### JEV-055: Instruction-policy contradiction review

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v1.0 | **Revised in:** v2.0 | **Disposition:** In scope: VRFY-001 and VRFY-004 (parity portion)

- **Primitive:** Pairwise Choice/Noul
- **Bind at:** Authored agent and shared-reference changes; Claude/Codex parity review
- **Required evidence:** Changed instruction clause and candidate governing contracts selected by paths/IDs.
- **Proposed behavior:** Detect semantic conflicts such as generic discovery versus a closed broker surface, or prose promising a different authority owner. Check every binding against the authoritative agent inventory and detect source prose that accidentally restores Codex parent synthesis or broadens broker-only roles.
- **Authority boundary:** Do not invent platform capabilities or modify frozen upstream/generated files; actual runtime qualification remains required. Preserve current host exceptions, effort and memory records; do not assume identical tool surfaces.
- **Measure:** Human-confirmed instruction contradictions caught before release.
- **Implementation note:** Consume current agent_inventory.json. Preserve the required named consensus-synthesizer on both native hosts.
- **Revision note:** Enriched for versioned decisions, incremental goal verification, or the refreshed host contract; original opportunity retained.
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-056, JEV-071
- **Sources:** S1, S2, S3, R1, R2

### Decision architecture and replay

#### JEV-056: Versioned Racecraft Decision Contract

**Priority:** P1 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-002

- **Primitive:** No model call; contract for all primitives
- **Bind at:** typesafe-mcp consumer contracts; delegation-runtime Jev adapters; SpecKit prepare/assess operations
- **Required evidence:** Current provider schemas, canonical source identities, rubric definitions, applicable policy and host authority records.
- **Proposed behavior:** Define one language-neutral contract with independent decision, projection, rubric, normalizer and policy versions; explicit evidence requirements, result types, observation binding, coverage and allowed advisory outcomes. Share test fixtures, not a new cross-language runtime.
- **Authority boundary:** The MCP remains a provider adapter. Domain IDs stay consumer-local unless an explicitly reviewed local-only extension is added. A decision result grants no permission and contains no executable command.
- **Measure:** Cross-language fixture conformance, unversioned behavior changes detected, and reduced duplicated policy logic.
- **Distinct contribution:** Promotes the baseline rubric/receipt sketch into the versioned decision unit; not another classifier.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** none beyond the shared foundation
- **Related:** JEV-005, JEV-023, JEV-053
- **Sources:** A1, T2, R2
- **Acceptance:**
  - Same input and policy version produce the same normalized advisory interpretation in Python and TypeScript fixtures.
  - No application correlation metadata is sent in the provider body.
  - Missing observation provenance cannot become verified execution or authorization.
  - A changed rubric or projection requires a new hash/version or validation fails.

#### JEV-057: Append-only decision and observation journal

**Priority:** P1 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-003

- **Primitive:** No model call; durable recordkeeping
- **Bind at:** delegation-runtime consumer return boundaries; SpecKit .process diagnostics and parent result consumption
- **Required evidence:** Genuine evaluation invocation/result references, source snapshot identity, complete normalized/raw answer references and policy interpretation.
- **Proposed behavior:** Append immutable, sequence-numbered decision observations alongside current stores. Record correlation/causation, run and aggregate revisions, complete/partial/not_run/error/stale states, and optional policy interpretations. Retain sensitive payloads in a separately controlled evidence store.
- **Authority boundary:** This is an additive audit journal, not a new authoritative event store. Do not dual-write and claim atomicity with legacy JSON. Hash chains are integrity aids, not authentication. A journal failure disables the optional semantic result, not existing evidence or authorized work.
- **Measure:** Traceability of actual decisions, detected missing records, crash recovery behavior and bounded storage growth.
- **Distinct contribution:** Adds durable sequencing and causality beyond a collection of individual receipts.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056
- **Related:** JEV-048, JEV-053
- **Sources:** A1, W1; 1 private delegation-runtime source(s) withheld
- **Acceptance:**
  - Duplicate delivery produces one logical observation.
  - Interrupted append is detectable; no partial record is interpreted as a completed judgment.
  - Worker-authored JSON cannot be promoted to an independently observed tool result.
  - Retention deletion leaves an explicit unavailable-evidence condition, not reconstructed text.

#### JEV-058: Historical and counterfactual decision replay

**Priority:** P1 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-003

- **Primitive:** Offline reducer/policy replay; live reevaluation is a separate opt-in mode
- **Bind at:** Shared evaluation harness; delegation-runtime and SpecKit recorded decision fixtures
- **Required evidence:** Stored judgments, verified evidence references, exact contract/policy versions and original context of application.
- **Proposed behavior:** Implement three distinct operations: reproduce original policy interpretation from stored answers; simulate another policy on those same answers; separately re-query a qualified model on recoverable, consented historical evidence. Compare outcome changes without executing them.
- **Authority boundary:** Offline replay cannot connect to a provider or mutate business state. Live reevaluation requires new consent/budget and is nondeterministic. Expired evidence makes a case non-reevaluable; a digest cannot recreate it. Counterfactual outcomes are not causal estimates of real workflow improvement.
- **Measure:** Reproducible original interpretations, policy-flip rates, replay coverage and no unintended effects.
- **Distinct contribution:** JEV-053 owns evaluation quality; this owns replay modes, records and execution isolation.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057
- **Related:** JEV-053, JEV-070
- **Sources:** A1, W1, D13
- **Acceptance:**
  - Offline modes make zero provider calls and zero dispatch/apply/push/resolve calls.
  - Unknown historical versions refuse replay rather than silently using current policy.
  - Original records remain byte-identical after counterfactual simulation.
  - Missing evidence is reported per case and never silently dropped from denominators.

#### JEV-059: Cross-repository causal handoff receipts

**Priority:** P1 | **Kind:** integration_protocol | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T4): second-host visibility and cross-repository causality; follow-on PRD

- **Primitive:** Deterministic protocol; optional semantic coverage annotations
- **Bind at:** SpecKit native parent and delegation-runtime dispatch/status/candidate boundary
- **Required evidence:** Workflow/run/task/dispatch IDs, parent-observed delegation-runtime response, source revision, candidate digest, acceptance IDs and existing execution observations.
- **Proposed behavior:** Map requested, admitted, started, report-settled, candidate-ready, applied and independently verified observations explicitly. Link a delegation-runtime report and its decision receipts to the originating SpecKit obligations, with stable correlation and causation IDs.
- **Authority boundary:** Do not infer goal completion from delegation-runtime completed status or candidate availability. Do not convert delegation-runtime evidence into SpecKit native TDD observations. Preserve consent, sandbox and apply authority in their existing owners.
- **Measure:** Lost or misattributed handoffs, false-complete imports, and duplicate/cancelled result handling.
- **Distinct contribution:** Defines the protocol joining workflow and delegated execution state, rather than another report grader.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057
- **Related:** JEV-024, JEV-036
- **Sources:** A1, S2; 1 private delegation-runtime source(s) withheld
- **Acceptance:**
  - Wrong run, task, checkout, revision or candidate digest is rejected or marked stale.
  - Out-of-order/duplicate/cancelled results cannot complete an obligation.
  - Candidate-ready is distinct from applied and verified.
  - No cross-repository global ordering or authenticated proof is claimed from a UUID alone.

#### JEV-060: Effect-intent reconciliation and duplicate prevention

**Priority:** P2 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Deterministic effect lifecycle; no Jev decision
- **Bind at:** Future event-driven dispatch/publication adapters; existing runner mutation/ledger boundaries
- **Required evidence:** An independently authorized operation, durable intent, provider/native request identity, observed result and current authoritative state.
- **Proposed behavior:** For explicitly approved event-driven effects, record intent and result separately with idempotency keys and reconciliation. Use a transactional outbox only inside a real shared transaction; otherwise expose dual-write gaps and unknown effects. Reuse existing command executors.
- **Authority boundary:** No new authority, automatic retries, generic event bus, or exactly-once network guarantee. Never blindly redispatch or repeat a GitHub mutation after a timeout. This is conditional hardening, not a prerequisite to shadow-only checks.
- **Measure:** Duplicate dispatch/publication attempts prevented and unresolved effects correctly checkpointed.
- **Distinct contribution:** Addresses replay/cross-process effect safety; not the existing semantic repair-family classification.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057, JEV-059
- **Related:** JEV-038, JEV-051
- **Sources:** A1, W2, S19
- **Acceptance:**
  - Crash after external success but before local result leads to read-only reconciliation, not replay.
  - A duplicate event does not reserve new work or spend.
  - Transaction rollback cannot publish an outbox item.
  - Unknown outcome remains unknown until the parent obtains genuine evidence.

### Continuous goal verification

#### JEV-061: Frozen goal and obligation registry

**Priority:** P1 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-008

- **Primitive:** Deterministic IDs/versions; optional atomic-criterion assistance
- **Bind at:** Autopilot kickoff/resume; PRD/Design Concept handoff; phase and task metadata
- **Required evidence:** Approved goals/non-goals, atomic acceptance criteria, authority provenance, existing FR/task IDs, required checks and current stage.
- **Proposed behavior:** Represent goals as frozen versioned obligations with source references, expected evidence, deterministic and semantic predicates, applicability conditions, owners and dependency edges. Derive stage-relative completion requirements without introducing another task scheduler.
- **Authority boundary:** The model cannot ratify, drop, weaken or silently add obligations. Unknown scope requires review. A /goal command is not assumed to exist in any host; this is an internal contract tied to existing workflows.
- **Measure:** Obligations omitted or altered during long runs and traceability to approved intent.
- **Distinct contribution:** Turns accepted requirements into stable runtime verification targets; JEV-009 improves wording, and JEV-023 checks task coverage.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056
- **Related:** JEV-008, JEV-009, JEV-023
- **Sources:** A1, X1, S4
- **Acceptance:**
  - Every required item has a source-backed stable ID and an owner.
  - Rewording does not change identity or repair allowance.
  - Goal changes are explicit versioned events and invalidate dependent judgments.
  - A planning stage never requires implementation evidence or labels implementation complete.

#### JEV-062: Incremental goal-completion verifier

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-009

- **Primitive:** Atomic Noul/Choice judgments plus deterministic conjunction
- **Bind at:** Trusted parent after consumed worker results, relevant artifact changes and before terminal handoff
- **Required evidence:** Frozen goal obligations; current relevant code/artifacts; genuine tool/test observations; previous judgments; unknown/in-flight effects.
- **Proposed behavior:** Assess each applicable obligation against supplied evidence as work progresses. Keep unsupported, contradicted, insufficient, stale and not_run results separate. Record a completion suggestion only when all required evidence is current and all existing gates have been independently satisfied.
- **Authority boundary:** No scalar is proof of done; response fluency, task settlement and checkboxes are not execution evidence. In shadow mode the result neither authorizes nor blocks work. Positive results never auto-apply, merge, close threads or stop the host. True shadow requires verdict isolation from the live decision-maker; a visible but non-enforcing result is advisory, not shadow.
- **Measure:** False completion per full workflow, missed obligations and useful early detection versus phase-end checking.
- **Distinct contribution:** Adds temporal goal verification inside execution; existing rows assess individual artifacts or handoffs.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057, JEV-061
- **Related:** JEV-005, JEV-023, JEV-036, JEV-064
- **Sources:** X1, A1, D13, D7
- **Acceptance:**
  - An empty required-obligation set yields invalid_goal, not vacuous completion.
  - One unjudged or missing required obligation prevents an unqualified completion suggestion.
  - Expected TDD RED is recognized from real stage evidence and does not trigger a repair loop.
  - An old positive result cannot survive a relevant source or goal change.
  - If native MCP exposes raw judgments to the live parent, report advisory_mode_required or use post-run evaluation; do not claim uncontaminated shadow evidence.

#### JEV-063: Change-triggered verification scheduler and invalidation

**Priority:** P1 | **Kind:** infrastructure | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-010

- **Primitive:** Deterministic scheduling/cache policy
- **Bind at:** Parent-observed lifecycle adapters; semantic preparation; run budget
- **Required evidence:** Qualified host boundary events, projection dependency hashes, in-flight evaluations, frozen goals, elapsed time and remaining authorized budget.
- **Proposed behavior:** Coalesce relevant changes, deduplicate identical projections and reevaluate only affected obligations. Use mandatory full dependency reconciliation at phase/terminal boundaries and when dependency coverage is unknown. Separate evaluation cache keys from policy-interpretation keys.
- **Authority boundary:** Do not install an unverified every-turn hook or bill on every tool callback. Clock values, correlation IDs and attempt IDs must not defeat content deduplication. Existing cancellation and run budgets dominate the scheduler.
- **Measure:** Useful checks per dollar, p95 end-to-end overhead, invalidation recall and duplicate call rate.
- **Distinct contribution:** Adapts the post’s every-turn idea to real host boundaries and change-aware cost control.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057, JEV-061, JEV-062
- **Related:** JEV-002, JEV-003, JEV-053
- **Sources:** X1, A1, D10
- **Acceptance:**
  - Repeated unchanged-state callbacks make no extra model call.
  - Unknown dependencies trigger full invalidation rather than optimistic reuse.
  - Late responses are marked stale after a new goal version or cancellation.
  - No status invocation, verifier event or journal append recursively schedules another check.
  - An offline scheduling simulation is not reported as live adapter latency or runtime qualification.

#### JEV-064: Premature-stop and redundant-continuation advice

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-011

- **Primitive:** Noul/Choice over goal evidence; deterministic eligibility
- **Bind at:** Autopilot pre-terminal summary and parent continuation decisions
- **Required evidence:** Stage-specific obligations, actual gate/verification receipts, unresolved/in-flight work and intended terminal claim.
- **Proposed behavior:** Warn when a proposed done message omits required work; conversely suggest finishing when approved scope and required evidence are already satisfied and further work would expand scope. Emit a bounded advisory with specific obligation IDs.
- **Authority boundary:** User cancellation and budget exhaustion always stop new work. No model-controlled Stop veto, unlimited continuation, silent skipping of gates, or auto-merge. The named synthesizer and other mandatory roles still run.
- **Measure:** Premature-completion rate and unnecessary post-goal work at fixed success criteria.
- **Distinct contribution:** Evaluates the decision to stop/continue, not just whether a report sounds responsive.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-061, JEV-062, JEV-063
- **Related:** JEV-028, JEV-036
- **Sources:** X1, A1, R1
- **Acceptance:**
  - A missing required test blocks only the semantic completion suggestion, not user cancellation.
  - All-goals-satisfied advice cannot bypass publication/UAT/approval obligations.
  - Provider outage does not trap a host Stop hook.
  - No pending source writes are hidden by a done recommendation.

#### JEV-065: Evidence-based stagnation and regression detection

**Priority:** P2 | **Kind:** semantic_judgment | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Noul/Choice on evidence deltas; counters in code
- **Bind at:** Long-running phases, delegated read results and remediation loops
- **Required evidence:** Successive source/evidence snapshots and obligation status changes, observed work stages, stable failure IDs and repair reservations.
- **Proposed behavior:** Flag repeated reports without new supporting evidence, reintroduced previously repaired defects, or activity unrelated to any approved obligation. Recommend a focused diagnostic or checkpoint rather than another identical attempt.
- **Authority boundary:** Probability fluctuation alone is not progress or regression. Do not penalize legitimate exploration or expected RED. No budget reset, forced termination, or replacement dispatch based solely on a score.
- **Measure:** Repeated ineffective work detected, false stagnation alarms and evidence-supported recovery outcomes.
- **Distinct contribution:** Uses a trajectory rather than a single failure classification.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-057, JEV-061, JEV-062, JEV-063
- **Related:** JEV-030, JEV-035
- **Sources:** X1, A1, D7
- **Acceptance:**
  - Unchanged files with genuinely new test/research evidence can count as progress.
  - New prose alone cannot close a failed obligation.
  - Reintroduced source defects invalidate prior satisfaction.
  - A probability wobble with identical evidence generates no regression event by itself.

#### JEV-066: Obligation-targeted verifier feedback packets

**Priority:** P1 | **Kind:** integration_protocol | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Semantic defect description already evaluated; deterministic ownership routing
- **Bind at:** Parent -> task/phase executor or required named synthesizer; delegation-runtime follow-up boundary
- **Required evidence:** Unmet obligation ID, grounded failure relation, minimal evidence, intended owner, original task scope and current shared reservation.
- **Proposed behavior:** Route each verifier concern back to the task/phase responsible with exact before/after evidence and a bounded correction target. Consolidate equivalent feedback without dropping dissent or original report IDs.
- **Authority boundary:** Do not auto-write, create a second repair budget or widen scope. Unknown/multiple owners return to the parent. Current consensus routing/security overrides and named synthesis remain mandatory.
- **Measure:** Repair precision, irrelevant redispatches, feedback duplication and repair-budget continuity.
- **Distinct contribution:** Defines targeted feedback delivery and lineage rather than only judging whether an existing fix worked.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-061, JEV-062
- **Related:** JEV-022, JEV-027, JEV-030, JEV-038
- **Sources:** X1, A1, R1
- **Acceptance:**
  - Feedback contains existing obligation and reservation IDs, never new budget identity.
  - Cross-owner concerns are serialized/reconciled by the parent.
  - Injected reviewer instructions are data, not feedback commands.
  - The synthesizer receives all material dissent with original evidence.

#### JEV-067: Budgeted verifier cascade and candidate comparison

**Priority:** P2 | **Kind:** experimental_optimization | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Noul/Choice comparisons; resource allocation in policy
- **Bind at:** Authorized alternative proposals; optional deeper review; evaluation harness
- **Required evidence:** Current unsatisfied obligations, separately generated candidates, their source/verification evidence and explicit candidate/compute budget.
- **Proposed behavior:** Evaluate cheap or parallel candidates on the same frozen obligations; request stronger reasoning only for unresolved consequential gaps within the existing approved budget. Compare equal-budget single-pass, frequent-verifier and cascaded strategies.
- **Authority boundary:** Do not silently spawn N workers, switch native/provider models, select a patch for application, or call ranking a correctness proof. Keep candidate generation independent of hidden holdout labels. All candidates retain uncertainty and coverage.
- **Measure:** Goal success at equal total cost/time, false selection, additional worker/tool overhead and incremental benefit of escalation.
- **Distinct contribution:** Extends a single escalation hint to controlled test-time-compute experiments and comparison of already authorized alternatives.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-005, JEV-053, JEV-058, JEV-062
- **Related:** JEV-020, JEV-031
- **Sources:** X1, D13, A1
- **Acceptance:**
  - A winner is not selected if required evidence is missing.
  - One weak critical obligation cannot be hidden by average score.
  - Speculative work counts against the same run budget.
  - No candidate is applied from verifier ranking alone.

#### JEV-068: Compaction and handoff obligation-preservation check

**Priority:** P1 | **Kind:** semantic_judgment | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Choice entailment plus per-obligation Noul
- **Bind at:** Parent-authored resume packet; compacted context; cross-agent summary
- **Required evidence:** Approved decisions, outstanding obligations, relevant original evidence, authority/budget records and candidate compacted handoff.
- **Proposed behavior:** Check that concise handoffs retain unresolved questions, negative results, source qualifications and constraints; recover omitted references before a new agent reasons from the summary. Preserve full records outside model context.
- **Authority boundary:** Do not replace native authority or reconstruct facts from a summary. Do not assume access to proprietary host compaction internals. Without a supported callback, validate only explicit parent-authored handoffs.
- **Measure:** Omitted obligations after compaction, invented commitments and resumed-work correctness.
- **Distinct contribution:** Targets loss during context reduction and resume, not ordinary generated-artifact fidelity.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-005, JEV-061
- **Related:** JEV-008, JEV-016, JEV-046
- **Sources:** A1, X1, D10
- **Acceptance:**
  - An unresolved failure remains unresolved after handoff.
  - Compressed text cannot turn an inference into explicit-human provenance.
  - Lost raw evidence is reported as unavailable.
  - Budget, consent and checkpoint state are read from their authoritative records, not the summary.

### Decision architecture and replay

#### JEV-069: Projection parity and recovery diagnostics

**Priority:** P2 | **Kind:** derived_view | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T4): second-host visibility and cross-repository causality; follow-on PRD

- **Primitive:** Offline deterministic projection; no model call
- **Bind at:** Decision timeline viewer; speckit-status; recovery tooling
- **Required evidence:** Journal entries and sequence coverage, canonical workflow/task/ledger snapshots and projection version.
- **Proposed behavior:** Derive a semantic-health timeline and compare it with current authoritative records. Show missing observations, stale projections, unknown effects and incompatible versions; assess whether eventual event-sourced migration would add operational value.
- **Authority boundary:** Do not replace authoritative snapshots, auto-repair stores, or infer unobserved past transitions. Status remains strictly read-only. A decision journal cannot reconstruct the entire business workflow without complete authoritative events.
- **Measure:** Detected drift, replay coverage, recovery diagnosis time and no unauthorized repairs.
- **Distinct contribution:** Adds recovery/parity evaluation beyond showing the latest semantic receipt.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-057, JEV-058
- **Related:** JEV-048, JEV-059
- **Sources:** A1, W1
- **Acceptance:**
  - A sequence gap is visible and never filled from model inference.
  - Read-only inspection changes no files or persistent cursors.
  - Unknown event versions are quarantined, not skipped as success.
  - A journal-only replay is explicitly scoped to semantic-health observations.

### Continuous goal verification

#### JEV-070: Sequential verifier calibration and anti-gaming evaluation

**Priority:** P1 | **Kind:** evaluation | **Introduced in:** bundle v2.0 | **Disposition:** In scope: VRFY-012

- **Primitive:** Offline trajectory evaluation; opt-in live judgments
- **Bind at:** JEV-053 holdout corpus, continuous-verifier rollout and model/rubric promotion
- **Required evidence:** Human-adjudicated complete trajectories, adversarial examples, intermediate judgments, actual stopping decisions and budget/accounting records.
- **Proposed behavior:** Evaluate false completion across whole runs, not just individual checks. Test repeated checking, score-shopping, stale positive reuse, adversarial summaries and negative evidence loss. Measure precision/recall, abstention, coverage and overhead under an unchanged stop policy. Keep verdicts hidden from the active baseline in a shadow arm; visible non-gating advice belongs to a separately labeled intervention arm.
- **Authority boundary:** Repeated outputs from one model are not independent evidence. A first high score or best-of-N score is not calibrated correctness. Never let the agent relabel the gold set, tune on holdout or weaken acceptance predicates.
- **Measure:** Run-level false completion, calibration drift, stop/continue error, reviewer overturns and end-to-end quality at a fixed budget.
- **Distinct contribution:** Adds sequential-decision failure modes that a static per-item rubric benchmark does not measure.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-053, JEV-058, JEV-062
- **Related:** JEV-064, JEV-067
- **Sources:** X1, D7, D13, A1
- **Acceptance:**
  - The same frozen trajectory is tested with phase-only and frequent checking.
  - All calls/attempts are retained, not only the favorable response.
  - Model alias changes require requalification; unknown resolved identity is explicit.
  - Small samples report uncertainty and are not described as production guarantees.

### Decision architecture and replay

#### JEV-071: Decision-policy invariant and crash-sequence testing

**Priority:** P2 | **Kind:** evaluation | **Introduced in:** bundle v2.0 | **Disposition:** Deferred (bundle tranche T5): conditional extension; needs the VRFY-012 calibration report

- **Primitive:** Deterministic state-machine tests; optional selected formal checker
- **Bind at:** Consumer policy reducers, decision journal and cross-repository adapters
- **Required evidence:** Closed observation/event vocabulary, versions, authority predicates, failure states and explicitly selected checking bounds.
- **Proposed behavior:** Test event sequences for duplicate delivery, revision races, cancellation, missing observations, journal failures and stale positive results. Optionally model the bounded policy in the existing formal-methods lane after operator selection.
- **Authority boundary:** Model checking proves only the encoded bounded properties, not Jev accuracy, native-host authentication or network exactly-once behavior. No new formal tool installation or weakening assumptions to get a pass.
- **Measure:** Invariant violations caught under generated sequences, crash recovery coverage and retained authority boundaries.
- **Distinct contribution:** Applies state-machine verification to the integration’s own policy and recovery behavior, not a user feature’s semantic property mapping.
- **Default mode:** off; shadow after explicit activation
- **Depends on:** JEV-056, JEV-057
- **Related:** JEV-059, JEV-060, JEV-063
- **Sources:** A1, W1, W2, S6
- **Acceptance:**
  - For any answer, missing authorization cannot produce an applied mutation.
  - For any sequence, offline replay emits no external effect.
  - Cancellation prevents new dispatch and stale results cannot reactivate the run.
  - A duplicate, stale or malformed observation cannot enlarge a repair allowance.

---

## Source index

Public sources cited above. Private delegation-runtime sources (nine entries in the bundle) are withheld; their findings are summarized under "Inherited findings to revalidate."

| Key | Title | Location |
|---|---|---|
| D1 | Jev introduction | `https://docs.typesafe.ai/introduction` |
| D2 | Noul | `https://docs.typesafe.ai/primitives/noul` |
| D3 | Choice | `https://docs.typesafe.ai/primitives/choice` |
| D4 | Score | `https://docs.typesafe.ai/primitives/score` |
| D5 | Confidence | `https://docs.typesafe.ai/confidence` |
| D6 | Models and limits | `https://docs.typesafe.ai/models` |
| D7 | Jev 1.13 jaggedness | `https://docs.typesafe.ai/model-jaggedness/jev-1.13` |
| D8 | Citation checking cookbook | `https://docs.typesafe.ai/cookbooks/citation_check` |
| D9 | Skill suggestion cookbook | `https://docs.typesafe.ai/cookbooks/skill_suggestion` |
| D10 | State | `https://docs.typesafe.ai/concepts/state` |
| D11 | Entity alignment cookbook | `https://docs.typesafe.ai/cookbooks/entity_alignment` |
| D12 | AutoResearch cookbook | `https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery` |
| T1 | MCP README | `https://github.com/racecraft-lab/typesafe-mcp/blob/1522e6dca5fb94585b33a221daef5825a20112dd/README.md` |
| T2 | MCP tool implementation | `https://github.com/racecraft-lab/typesafe-mcp/blob/1522e6dca5fb94585b33a221daef5825a20112dd/cmd/evaluate/tools.go` |
| T3 | Plugin installation and defaults | `https://github.com/racecraft-lab/typesafe-mcp/blob/1522e6dca5fb94585b33a221daef5825a20112dd/docs/plugin.md` |
| T4 | Typed-judgments skill | `https://github.com/racecraft-lab/typesafe-mcp/blob/1522e6dca5fb94585b33a221daef5825a20112dd/plugin/shared-skills/typed-judgments/SKILL.md` |
| T5 | Plugin launcher | `https://github.com/racecraft-lab/typesafe-mcp/blob/1522e6dca5fb94585b33a221daef5825a20112dd/plugin/bin/evaluate-launch` |
| S1 | Repository contribution and generated-artifact contract | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/AGENTS.md` |
| S2 | Autopilot entrypoint | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/SKILL.md` |
| S3 | Capability discovery | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` |
| S4 | Gate validation | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/gate-validation.md` |
| S5 | Artifact review handoff | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/artifact-review.md` |
| S6 | Formal checkpoints | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/formal-methods.md` |
| S7 | Post-implementation | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/post-implementation.md` |
| S8 | Memory policy | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-autopilot/references/subagent-memory-policy.md` |
| S9 | Resolve PR | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-resolve-pr/SKILL.md` |
| S10 | Grill Me | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/grill-me/SKILL.md` |
| S11 | PRD authoring | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-prd/SKILL.md` |
| S12 | Ubiquitous language | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/ubiquitous-language/SKILL.md` |
| S13 | Coach | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-coach/SKILL.md` |
| S14 | Scaffold | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-scaffold-spec/SKILL.md` |
| S15 | Status | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-status/SKILL.md` |
| S16 | Archive cleanup | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-archive-cleanup/SKILL.md` |
| S17 | Install | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-install/SKILL.md` |
| S18 | Upgrade | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills/speckit-upgrade/SKILL.md` |
| S19 | Helper registry | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/speckit_pro_runner/helpers/registry.py` |
| S20 | Artifact author | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/agents/artifact-author.md` |
| S21 | Existing MCP registration | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/.mcp.json` |
| S22 | Pinned Claude skill inventory | `https://github.com/racecraft-lab/racecraft-plugins-public/tree/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/skills` |
| S23 | Pinned Codex skill inventory | `https://github.com/racecraft-lab/racecraft-plugins-public/tree/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/codex-skills` |
| S24 | Pinned Claude agent inventory | `https://github.com/racecraft-lab/racecraft-plugins-public/tree/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/agents` |
| S25 | Pinned Codex agent inventory | `https://github.com/racecraft-lab/racecraft-plugins-public/tree/5abb6f8f2599a2b300a782ec6a659a026f0e3dd8/speckit-pro/codex-agents` |
| A1 | User-provided Racecraft + Jev: State -> Judgment -> Event architecture note | Supplied architecture note (HTML, in the handoff bundle); not committed |
| X1 | omarsar0: Jev verifier for a custom /goal harness feature | `https://x.com/omarsar0/status/2101443311454036477`; core text retrieved, trailing content and performance claims not verified |
| D13 | TypeSafe SDE cascade cookbook | `https://docs.typesafe.ai/cookbooks/sde_cascade` |
| W1 | Microsoft Azure Architecture Center: Event Sourcing pattern | `https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing` |
| W2 | AWS Prescriptive Guidance: Transactional outbox pattern | `https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html` |
| R1 | SpecKit agent capability parity commit / PR #583 | `https://github.com/racecraft-lab/racecraft-plugins-public/commit/f49c0e91537d9da4db5c5c38ecad2416b6142d6a` |
| R2 | Authoritative SpecKit agent inventory | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/f49c0e91537d9da4db5c5c38ecad2416b6142d6a/speckit-pro/speckit_pro_runner/agent_inventory.json` |
| R3 | Current repository agent instructions and validation commands | `https://github.com/racecraft-lab/racecraft-plugins-public/blob/f49c0e91537d9da4db5c5c38ecad2416b6142d6a/AGENTS.md` |


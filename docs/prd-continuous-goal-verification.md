# PRD: Continuous Goal Verification for SpecKit Pro

**Status**: Draft
**Source**: Jev / SpecKit Pro integration handoff bundle v2 (`speckit-pro-jev-integration-blueprint-v2.md`, `speckit-pro-jev-integration-backlog-v2.json`, `speckit-pro-jev-coding-agent-handoff-v2.md`, dated 2026-09-19) plus a four-question scoping interview on 2026-09-19
**Created**: 2026-09-19
**Last updated**: 2026-09-19
**Target window**: Foundation and first pilots within the next two releases; goal verifier promoted from shadow only after the VRFY-012 calibration report exists
**Spec ID prefix**: `VRFY-###` (Verification)

---

## 1. Problem

> "How does SpecKit Pro tell work that is actually complete from work that merely looks complete?"

Autopilot today decides completion from signals that a fluent agent can satisfy without doing the work: a self-rated five-criterion confidence composite, tasks marked `[X]`, an FR identifier appearing in a task title, a review thread reply that sounds like a fix, and a terminal summary that says "all tests pass." Deterministic gates catch structural defects (missing markers, malformed frontmatter, path drift), but nothing checks the semantic relationship between a requirement and the evidence offered for it. The failure shows up late: reviewers reopen threads, UAT finds requirements nobody planned for, and archive summaries describe work that never shipped.

The `typesafe-jev` plugin (0.7.0, built from the same `typesafe-mcp` revision the bundle inspected) already exposes one `evaluate` MCP tool that answers bounded semantic questions with calibrated probabilities. Shipped SpecKit Pro source contains no reference to it. The handoff bundle catalogs 71 ways to use it. This PRD selects the 13 backlog items that attack run-level false completion, delivers them as twelve features (two items split across specs, two specs share an item), and defers the other 58 with reasons.

## 2. Goals & Non-goals

### 2.1 Goals

- Every semantic judgment SpecKit Pro consumes is a versioned, replayable decision with separate identities for evidence projection, rubric, normalizer, and policy, so a changed prompt or model alias is a detectable contract change rather than silent drift.
- Autopilot records, at parent-observed boundaries, which approved obligations have current supporting evidence and which do not, and can say so in a terminal advisory without gaining any new authority to stop, continue, apply, or publish.
- Three existing evidence handoffs (requirement-to-task coverage, review-fix closure, claim-to-source support) receive shadow annotations that preserve the original output and never change a gate result.
- Both Claude Code and Codex hosts consume the same decision contracts, rubric catalog, and policy through their own qualified adapters, with the named `consensus-synthesizer` preserved on both.
- Offline modes make zero provider calls, and the default-disabled path is byte-identical to today's behavior, so the integration can ship before any live evaluation is authorized.
- A frozen, human-labeled trajectory corpus and calibration report exist before any check is promoted from shadow to advisory.

### 2.2 Non-goals (out of scope)

The bundle's 71 opportunities were filtered to 13 in-scope items, delivered by the twelve features below. Every one of the 58 excluded identifiers is listed here with the reason, so the cut is auditable. The full per-item record for all 71 (surfaces, evidence, behavior, boundary, metric, dependencies, disposition) lives in the [backlog catalog](ai/specs/continuous-goal-verification-backlog.md), which replaces the external handoff bundle as the source of record for future specs.

| Group | Backlog IDs | Reason for deferral |
|---|---|---|
| Second-host visibility and cross-repository causality (bundle tranche T4) | JEV-048, JEV-059, JEV-069, JEV-055 beyond the parity check folded into VRFY-001 and VRFY-004 | JEV-048 renders receipts that VRFY-003 does not yet produce; JEV-059 and JEV-069 couple this public repository to a separate delegation runtime and need a cross-repo decision. Follow-on PRD. |
| Conditional extensions (bundle tranche T5) | JEV-060, JEV-065, JEV-066, JEV-067, JEV-068, JEV-071 | Each needs the VRFY-012 calibration report to justify its budget. JEV-060 applies only if an event-driven mutation is ever approved. Follow-on PRD. |
| Original catalog, P2 in source | JEV-001, 006, 007, 012, 014, 020, 024, 026, 027, 029, 030, 031, 035, 039, 040, 042, 045, 046, 047, 049, 050, 051, 054 | The source marks these "validate value first." None addresses run-level false completion. |
| Original catalog, P1 single-artifact checks not selected | JEV-002, 003, 004, 008, 009, 010, 011, 013, 015, 016, 017, 018, 019, 021, 022, 025, 028, 032, 033, 034, 036, 037, 041, 043, 044, 052 | Each is one more consumer of the same eight rubric families. They become cheap once VRFY-004 exists and each needs its own measured baseline. Adding them now multiplies surfaces without adding a new capability. |

Also out of scope, permanently for this PRD:

- Any new authority. A Jev result never authorizes implementation, suppresses a required check, applies a patch, opens or merges a PR, resolves a thread, or ends a session.
- A second provider client. Credentials, provider selection, HTTP, retries, and validation stay in `typesafe-mcp`.
- An event-sourcing rewrite of workflow state. The decision journal is additive diagnostic history.
- Expanding sweep-worker capabilities. Sweep roles keep their closed broker surface.
- Paid Jev calls in ordinary CI or unit tests.

## 3. Acceptance Criteria

### 3.1 Host Boundary and Implementation-Map Spike *(-> VRFY-001)*

- **AC-1.1**: A spike report records actual HEAD, the authoritative `agent_inventory.json` role set, the helper registry envelope, and the exact file and line integration points for prepare, invoke, consume, and record on both Claude Code and Codex.
- **AC-1.2**: For each host, the report states whether the native `evaluate` result is visible to the live parent before its decisions are sealed, and classifies the achievable pilot posture as `isolated_shadow`, `retrospective_shadow`, or `advisory_not_authorized`.
- **AC-1.3**: The report records how the `typesafe-jev` plugin is registered on each host today (the plugin ships a Claude MCP config; the Codex registration path must be observed, not assumed) and names any qualification gap.
- **AC-1.4**: The report classifies each inherited bundle finding against current source as still open, resolved, or unverified, including review-thread pagination and resolve-before-verify ordering in `speckit-resolve-pr`.
- **AC-1.5**: The spike changes no shipped source, installs nothing into user registries, and makes no provider call.

### 3.2 Versioned Decision Contract and Offline Prepare/Assess *(-> VRFY-002)*

- **AC-2.1**: A language-neutral JSON contract defines `decision_id`/`decision_version`, projection id/version/hash, rubric id/version/hash, normalizer version plus provider-fixture version, policy id/version/hash, preconditions, and `authority_owner`; a conformance fixture set exercises it.
- **AC-2.2**: Registered runner operations `prepare-semantic-check` and `assess-semantic-check` exist in the helper registry with promotion status and request fixtures, and no skill instructs their use before registration.
- **AC-2.3**: The wire projection sends only provider-supported `state`, `questions`, and selected model fields; local run, workflow, correlation, and consent identities are excluded, and a test proves it.
- **AC-2.4**: Normalization handles Noul, Choice, and Score separately; malformed JSON, duplicate keys, non-finite numbers, unknown options, omitted answers, refusals, and unknown model identity each produce an explicit non-success state and never a positive judgment.
- **AC-2.5**: Receipts keep `execution_status`, `coverage`, `semantic_outcomes`, `freshness`, `provenance`, and `policy_interpretation` as separate fields; `execution_status=complete` means the request was answered, not that a goal is complete.
- **AC-2.6**: Canonicalization is versioned, rejects duplicate keys and non-finite values, preserves evidence bytes, and measures actual serialized UTF-8 size. The 64k total and 32k state-plus-longest-question token budgets are checked with an explicitly labeled estimate (or a qualified tokenizer when available), never equated with the byte count; the receipt records which was used, and the provider's own enforcement remains the backstop.
- **AC-2.7**: The initial rubric catalog uses string instructions and criteria only, so it runs on both the direct TypeSafe and OpenRouter backends.

### 3.3 Additive Decision Journal and Offline Replay *(-> VRFY-003)*

- **AC-3.1**: Logical events `DecisionRequested`, `DecisionSkipped`, `DecisionEvaluated`, `DecisionFailed`, `DecisionMarkedStale`, and `PolicyInterpreted` (or an existing equivalent vocabulary) are appended with per-run sequence, event id, correlation and causation ids, source revision, and contract identities.
- **AC-3.2**: Duplicate delivery yields one logical observation; an interrupted append is detectable; a partial record is never read as a completed judgment; worker-authored JSON cannot be promoted to an observed tool result.
- **AC-3.3**: Sensitive payloads live in a separately controlled evidence store; the journal holds a reference and digest; deletion leaves an explicit unavailable-evidence marker.
- **AC-3.4**: Historical replay reproduces the original interpretation from stored answers and original policy version, refuses unknown versions, and leaves original records byte-identical.
- **AC-3.5**: Counterfactual policy simulation reports hypothetical differences without editing records or taking any action.
- **AC-3.6**: Both offline modes make zero provider, dispatch, apply, push, or resolve calls, proven by test.
- **AC-3.7**: Live model reevaluation exists only as a guarded refusal interface until VRFY-012 supplies an authorized manifest.
- **AC-3.8**: A crash after send but before record leaves the request marked unknown; no automatic retry is billed on the assumption it failed.

### 3.4 Dual-Host Trusted-Parent Adapter with Consent, Budget, and Egress Controls *(-> VRFY-004)*

- **AC-4.1**: Capability discovery lists an optional typed-semantic-judgment capability without a hardcoded vendor preference; the trusted parent on each host invokes the already-registered `evaluate` tool.
- **AC-4.2**: Per-project enablement defaults to off; with it off, the runner introduces no provider request, credential discovery, new diagnostic write, or changed gate or dispatch result, proven by a byte-comparison test of existing fixtures.
- **AC-4.3**: Before each outbound request the adapter checks project consent, provider and model pairing, permitted data classes, and remaining call, input, spend, and time budget; a failure skips the optional call and records `DecisionSkipped`.
- **AC-4.4**: Requested and reported model identities are both recorded; the rubric catalog pins `jev-1.13.0`, and a differing reported identity marks the result `unqualified`.
- **AC-4.5**: Sweep roles gain no `evaluate` access, secrets, or filesystem scope; a test asserts the agent inventory and role allowlists are unchanged.
- **AC-4.6**: Claude Code and Codex adapters pass the same contract fixtures, and a parity test proves the named `consensus-synthesizer` binding and all current gates, budgets, and permissions are preserved on both hosts.
- **AC-4.7**: Key values never appear in runner output, journal entries, or test logs.

### 3.5 Pilot: Requirement-to-Task Semantic Coverage *(-> VRFY-005)*

- **AC-5.1**: After Tasks (G5), each source-backed atomic requirement or acceptance id receives one Noul asking whether the linked task set plans the behavior, with planned behavior, failure cases, and required evidence recorded separately.
- **AC-5.2**: The existing structural G5 helper remains authoritative; the semantic result is an annotation that changes no gate outcome, task count, or repair reservation.
- **AC-5.3**: One uncovered required obligation is reported as uncovered regardless of how many others are covered; inapplicability comes only from approved scope rules, never from a low score.
- **AC-5.4**: A relevant plan or task edit marks dependent coverage judgments stale.
- **AC-5.5**: Fixtures cover a task that only repeats the FR id, a paraphrased plan, a missing sub-obligation, and planning coverage wrongly presented as implementation completion.

### 3.6 Pilot: Review-Fix Closure Verification with Deterministic Prerequisites *(-> VRFY-006)*

- **AC-6.1**: `speckit-resolve-pr` fetches all review-thread and comment pages before claiming all feedback is handled, and posts replies and resolves threads only after final verification and confirmed pushed SHA.
- **AC-6.2**: For each thread, a closure judgment consumes the original concern, full thread, before and after source, acceptance condition, actual verification observations, and pushed SHA, and records whether the concern was addressed or rebutted with evidence.
- **AC-6.3**: The judgment is an annotation only; no reply or resolution is made from a model result, and missing verification cannot become `resolved`.
- **AC-6.4**: A later relevant edit invalidates the closure judgment.
- **AC-6.5**: Fixtures cover a fix to the wrong path, a superficially similar edit, a correct fix without execution evidence, a supported false-positive rebuttal, an omitted comment, and a new regression.

### 3.7 Pilot: Claim-to-Source Support Annotation *(-> VRFY-007)*

- **AC-7.1**: At the shared grounding boundary, quote existence is established mechanically first; only then is a Choice with `supports`, `contradicts`, `does_not_address`, and `insufficient_context` asked over the exact claim and retrieved span.
- **AC-7.2**: Output is an annotation linked to the original finding; the finding is never rewritten or suppressed, and the full distribution is retained.
- **AC-7.3**: A later source edit marks affected support judgments stale.
- **AC-7.4**: Fixtures cover a real but irrelevant citation, paraphrased support, opposite behavior, missing branch context, a missing source, and prompt-like instructions embedded in evidence.

### 3.8 Frozen Goal and Obligation Registry *(-> VRFY-008)*

- **AC-8.1**: At kickoff or resume, approved goals become versioned obligations with stable id, goal version, source reference and provenance class, owning phase or task, applicability rule, required authoritative observations, semantic predicates, and dependency references, reusing existing FR and task ids.
- **AC-8.2**: An empty applicable required set is rejected as `invalid_goal`; a legitimate no-op stage needs an explicit existing workflow contract.
- **AC-8.3**: Obligations are stage-relative: a planning-stage goal never requires implementation evidence or labels implementation complete; publication, UAT, rendering, and human approval keep independent evidence requirements.
- **AC-8.4**: Rewording does not change identity or repair allowance; a goal change is an explicit versioned event that invalidates dependent judgments; the model cannot add, drop, or weaken an obligation.

### 3.9 Phase-Boundary Goal-Completion Verifier *(-> VRFY-009)*

- **AC-9.1**: At phase handoff and proposed terminal summary, the trusted parent reconciles the complete applicable obligation set, not only items previously checked.
- **AC-9.2**: The aggregator emits `invalid_goal`, `known_unmet_obligation_ids`, `missing_authoritative_evidence_ids`, `unjudged_or_uncertain_semantic_ids`, `stale_assessment_ids`, `unresolved_effects`, `mandatory_work_still_pending`, and `completion_suggestion_eligible`; no field hides another.
- **AC-9.3**: Eligibility is true only when the goal is valid, every applicable required obligation has current required observations and an acceptable semantic assessment under its versioned rubric and policy, no required effect is unknown, and the stage's mandatory work is satisfied. It remains a suggestion, never a gate result.
- **AC-9.4**: Expected TDD RED is recognized from the genuine test stage and does not trigger corrective work.
- **AC-9.5**: The existing G6.5 confidence block and the named synthesizer are unchanged; Jev distribution confidence is never substituted for the composite score.
- **AC-9.6**: On a host where the `evaluate` result is visible to the live parent, the run is labeled `advisory_mode_required` and shadow evidence is collected only offline or post-run.

### 3.10 Change-Triggered Scheduler and Invalidation *(-> VRFY-010)*

- **AC-10.1**: Only parent-observed boundaries schedule checks: consumed worker results after effect reconciliation, relevant source, task, test, or goal changes, phase handoffs, terminal summaries, and cancellation or revoked consent.
- **AC-10.2**: A repeated unchanged-state callback creates no extra evaluation; evaluation and interpretation cache keys exclude timestamps, attempt ids, and correlation ids.
- **AC-10.3**: Unknown dependency coverage invalidates the conservative larger scope; a late response after cancellation, goal revision, or supersession is retained as stale and never applied.
- **AC-10.4**: One in-flight check per decision, projection, and run identity; a verifier result, journal append, or status render never recursively schedules another check.
- **AC-10.5**: Existing cancellation and run budgets dominate the scheduler; budget exhaustion never becomes success.

### 3.11 Premature-Stop and Redundant-Continuation Advice *(-> VRFY-011)*

- **AC-11.1**: Before a terminal summary, a premature-done advisory names the exact unsatisfied obligation ids and missing evidence; a redundant-continuation advisory names the satisfied goal and the out-of-scope proposed work.
- **AC-11.2**: Neither advisory ends a session, loops a worker, switches models, resets a budget, skips a gate, or bypasses publication, UAT, or approval obligations; user cancellation always wins.
- **AC-11.3**: The advisory carries stable obligation and evidence references for diagnosis and no executable command; it does not build a second repair dispatcher.
- **AC-11.4**: Provider outage never traps a host stop path, and no pending source write is hidden by a done recommendation.

### 3.12 Trajectory Corpus, Calibration Report, and Gated Live Evaluation *(-> VRFY-012)*

- **AC-12.1**: A frozen, human-labeled trajectory corpus with intermediate goals, evidence, revisions, results, and proposed termination points exists under the test tree, split into development and holdout sets, with labels held separately from model outputs.
- **AC-12.2**: Offline replay compares phase-end verification with change-triggered verification on the same trajectories at equal permitted work, and reports run-level false completion, early missed-obligation detection, false alarms, unnecessary continuation, coverage, and total overhead, with uncertainty on every rate.
- **AC-12.3**: Every attempt, refusal, and unavailable case is retained; repeated same-state queries are rejected as score shopping; the holdout is never used to tune thresholds.
- **AC-12.4**: Live evaluation requires an explicit test manifest naming repository and data consent, provider and pinned model, permitted hosts, request, spend, and time caps, failure behavior, fixed corpus, and reviewed success criteria; default caps authorize zero live requests and CI denies provider egress even when credentials exist.
- **AC-12.5**: Promotion of any check from shadow to advisory is recorded as a reviewed decision citing this report; the report never substitutes for deterministic release gates.

## 4. Migration Path (phased, one phase per SPEC)

- **Phase 1 (VRFY-001) - Spike**: Map both hosts before touching shipped source; settle the shadow-versus-advisory question per host.
- **Phase 2 (VRFY-002) - Decision contract**: Pure offline foundation; no authority, no network.
- **Phase 3 (VRFY-003, VRFY-008) - Journal and obligations**: Parallel. Both consume the contract; neither needs a provider.
- **Phase 4 (VRFY-004) - Dual-host adapter**: The only slice that touches the wire, default disabled, both hosts qualified together.
- **Phase 5 (VRFY-005, VRFY-006, VRFY-007, VRFY-009) - Pilots and phase-boundary verifier**: Parallel consumers of the adapter; each inserts at an existing handoff.
- **Phase 6 (VRFY-010) - Scheduler**: Incremental checking between boundaries.
- **Phase 7 (VRFY-011, VRFY-012) - Advice and calibration**: The user-visible payoff and the evidence needed to promote it.

## 5. Module and Interface Deltas

| Feature (§3) | Module or interface | Delta | Note |
|---|---|---|---|
| Host Boundary Spike | `docs/ai/specs/continuous-goal-verification-host-boundary-spike.md` | new | Report only; no shipped source change |
| Decision Contract | `speckit-pro/speckit_pro_runner/semantic_checks.py` | new | Prepare, normalize, assess, canonicalize |
| Decision Contract | `speckit-pro/speckit_pro_runner/contracts/semantic-decision-*.json` | new | Decision, envelope, receipt schemas |
| Decision Contract | `speckit-pro/speckit_pro_runner/helpers/registry.py` | changed | Registers `prepare-semantic-check`, `assess-semantic-check` |
| Decision Contract | shared rubric catalog under `speckit-pro/` | new | Versioned, string-only questions |
| Journal and Replay | `speckit-pro/speckit_pro_runner/decision_journal.py` | new | Append, replay, simulate; evidence-store reference |
| Journal and Replay | `<feature>/.process/decision-journal/` | new | Diagnostic records; not authoritative |
| Dual-Host Adapter | `speckit-pro/skills/speckit-autopilot/references/capability-discovery.md` | changed | Optional typed-semantic-judgment capability |
| Dual-Host Adapter | `speckit-pro/skills/speckit-autopilot/references/semantic-checks.md` | new | Ownership, consent, budgets, failure behavior |
| Dual-Host Adapter | Claude and Codex autopilot skill bindings | changed | Thin invoke-and-consume at existing handoffs |
| Dual-Host Adapter | project semantic-check configuration | new | Enablement, consent, data classes, caps; default off |
| Requirement-to-Task Coverage | Tasks phase G5 handoff | changed | Adds shadow annotation beside structural result |
| Review-Fix Closure | `speckit-pro/skills/speckit-resolve-pr/SKILL.md` | changed | Full pagination; verify, push, then reply and resolve |
| Review-Fix Closure | `speckit-pro/speckit_pro_runner/helpers/` sweep or review helper | changed | Closure annotation record |
| Claim-to-Source Support | shared grounding boundary reference | changed | Support annotation queue |
| Obligation Registry | `speckit-pro/speckit_pro_runner/goal_obligations.py` | new | Frozen obligations, versions, applicability |
| Obligation Registry | `<feature>/.process/goal-obligations.json` | new | Versioned goal record |
| Phase-Boundary Verifier | `speckit-pro/speckit_pro_runner/goal_verifier.py` | new | Reconciliation and aggregation vector |
| Phase-Boundary Verifier | autopilot phase-handoff and terminal-summary references | changed | Consume verifier output as advisory |
| Scheduler | `speckit-pro/speckit_pro_runner/goal_verifier.py` | changed | Dirty tracking, coalescing, single-flight, invalidation |
| Stop/Continue Advice | autopilot pre-terminal summary reference | changed | Advisory block with obligation ids |
| Trajectory Calibration | `tests/speckit-pro/trajectories/` | new | Frozen corpus, holdout, replay report |
| Trajectory Calibration | live-evaluation test manifest schema | new | Zero-default caps |

## 6. Constraints

- Constitution: Python 3.11+ standard library only for repository tooling; no active Bash or `jq`; Layer 4 unit coverage before merge; source under `speckit-pro/` with regenerated payloads; release-please owns versions.
- Both hosts, the whole way: every contract, rubric, and policy ships for Claude Code and Codex together; `agent_inventory.json` is the authoritative role set; the named `consensus-synthesizer` is preserved on both.
- No new authority; no second provider client; explicit egress and spend consent per project; sweep workers keep their closed broker surface; exact checks stay exact; existing budgets and repair ownership unchanged; no event-sourcing rewrite; disabled path is byte-identical; no unsupported claims (fixture, mocked transport, native observation, and live evaluation are distinct evidence classes). These are the bundle's ten non-negotiable boundaries and bind every VRFY spec.
- Jev facts at 2026-09-19: current model `jev-1.13.0`; aliases move, so the rubric catalog pins the versioned id and records the reported id; 64k tokens for state plus questions and 32k for state plus the longest question; text-only; literal reading, weak counting, distractor sensitivity, and adversarial-state susceptibility are documented, so identities, counts, and permissions stay in code.
- The OpenRouter backend accepts only string instructions and criteria; the plugin defaults to that backend, so the shared rubric format is string-only.
- A local stdio MCP server is not local inference: state leaves the machine. Path exclusions and secret filtering run in code before transmission.
- Shadow evidence requires information isolation. A verdict visible to the live parent is advisory, not shadow, and is evaluated as a separate intervention arm.
- Test fixtures live under `tests/speckit-pro/` and never read a `specs/<feature>/` path at run time.

## 7. Open Questions

- **OQ-1 (VRFY-001):** Is the native `evaluate` result visible to the live parent on each host? Recommendation: assume yes until observed otherwise, plan retrospective shadow for the pilots, and treat `isolated_shadow` as a qualification to earn.
- **OQ-2 (VRFY-001, VRFY-004):** The `typesafe-jev` plugin ships a Claude MCP config but no Codex config in the installed cache. Which Codex registration path is qualified, and does it need a change in `typesafe-mcp` first? Recommendation: qualify manual MCP registration on Codex in the spike; do not fork the launcher into SpecKit.
- **OQ-3 (VRFY-003):** JSON-lines under `.process/` or standard-library SQLite for the journal? Recommendation: JSON-lines using the existing atomic-write helpers; adopt SQLite only if concurrency tests fail.
- **OQ-4 (VRFY-003):** Retention and access rules for the evidence store. Recommendation: per-feature directory, gitignored, bounded by size, with an explicit unavailable marker on expiry.
- **OQ-5 (VRFY-004):** Where does per-project consent and budget configuration live? Recommendation: a project-level file alongside existing preset configuration, read-only from status mode.
- **OQ-6 (VRFY-010):** Which lifecycle events does each host actually expose to the trusted parent? Recommendation: start with the four boundaries the autopilot references already name; never assume an after-turn hook.
- **OQ-7 (VRFY-012):** Source of the first human-labeled trajectories. Recommendation: replay archived VRFY-005 through VRFY-009 shadow runs from this repository's own specs, labeled by a maintainer, before any external corpus.

## 8. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Host Boundary and Implementation-Map Spike | AC-1.* | VRFY-001 | - | P1 |
| Versioned Decision Contract and Offline Prepare/Assess | AC-2.* | VRFY-002 | VRFY-001 | P1 |
| Additive Decision Journal and Offline Replay | AC-3.* | VRFY-003 | VRFY-002 | P1 |
| Dual-Host Trusted-Parent Adapter with Consent, Budget, and Egress Controls | AC-4.* | VRFY-004 | VRFY-002, VRFY-003 | P1 |
| Pilot: Requirement-to-Task Semantic Coverage | AC-5.* | VRFY-005 | VRFY-004 | P1 |
| Pilot: Review-Fix Closure Verification with Deterministic Prerequisites | AC-6.* | VRFY-006 | VRFY-004 | P1 |
| Pilot: Claim-to-Source Support Annotation | AC-7.* | VRFY-007 | VRFY-004 | P2 |
| Frozen Goal and Obligation Registry | AC-8.* | VRFY-008 | VRFY-002 | P1 |
| Phase-Boundary Goal-Completion Verifier | AC-9.* | VRFY-009 | VRFY-003, VRFY-004, VRFY-008 | P1 |
| Change-Triggered Scheduler and Invalidation | AC-10.* | VRFY-010 | VRFY-009 | P1 |
| Premature-Stop and Redundant-Continuation Advice | AC-11.* | VRFY-011 | VRFY-010 | P1 |
| Trajectory Corpus, Calibration Report, and Gated Live Evaluation | AC-12.* | VRFY-012 | VRFY-003, VRFY-009, VRFY-010 | P1 |

## 9. Success Criteria

1. All acceptance criteria AC-1.1 through AC-12.5 pass, each SPEC within its reviewability budget.
2. With enablement off, existing fixture outputs, gate results, status-mode writes, and workflow artifacts are byte-identical to the pre-integration baseline; generated payloads regenerate per the artifact contract.
3. Offline replay and both pilot fixture suites run with zero provider, dispatch, apply, push, or resolve calls, enforced by test.
4. Claude Code and Codex pass the same contract, parity, and synthesizer-preservation fixtures.
5. A VRFY-012 calibration report exists for at least one frozen holdout and is cited by any decision to promote a check beyond shadow.
6. The originating question in §1 is answerable from a run's terminal advisory by obligation id.

## 10. References

- **Technical roadmap:** `docs/ai/specs/continuous-goal-verification-technical-roadmap.md`
- **Roadmap MOC:** `docs/ai/specs/continuous-goal-verification-roadmap-MOC.md`
- **Backlog catalog:** `docs/ai/specs/continuous-goal-verification-backlog.md`, the committed per-item record for JEV-001 through JEV-071 and the procedure for turning a deferred entry into a spec
- **Constitution:** `.specify/memory/constitution.md`
- **Project standards:** `AGENTS.md`, `REVIEW.md`
- **Discovery source:** Jev / SpecKit Pro integration handoff bundle v2, 2026-09-19 (blueprint, backlog JSON, coding-agent handoff, supplied architecture note); superseded by the backlog catalog above
- **Provider documentation:** TypeSafe Jev models and limits, Jev 1.13 jaggedness, and confidence pages at `docs.typesafe.ai`, read 2026-09-19
- **Existing MCP registration:** `speckit-pro/.mcp.json` (sweep broker only today)
- **Authoritative role inventory:** `speckit-pro/speckit_pro_runner/agent_inventory.json`

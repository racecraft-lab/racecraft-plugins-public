# PRD: Codex GPT-5.6 Agent Routing

**Status**: Active - not yet implemented
**Source**: Maintainer request plus official OpenAI documentation, `$research`,
and `$tavily-research` passes completed 2026-07-09
**Created**: 2026-07-09
**Last updated**: 2026-07-09
**Target window**: Next SpecKit Pro minor release after the active XPLAT-009
installer/runtime surface is stable

---

## 1. Problem

> "How should SpecKit Pro route each Codex agent to GPT-5.6 Sol, Terra, or
> Luna - and to which reasoning effort - so consumers get the best reliable
> result at the lowest measured cost?"

SpecKit Pro currently defines ten Codex custom agents. Nine source TOMLs pin
`gpt-5.5`; the latency-first helper pins `gpt-5.3-codex-spark`. Effort is mostly
`xhigh`, with two read-only analysts at `low` and the Spark helper omitting an
effort field. The installer and structural tests also encode a mostly uniform
model policy. That policy cannot take advantage of the GPT-5.6 family's
role-specific price/capability tiers, and the current Layer 6 Codex harness
sweeps effort while holding the TOML model constant.

OpenAI positions `gpt-5.6-sol` as the flagship tier,
`gpt-5.6-terra` as the intelligence/cost balance, and `gpt-5.6-luna` for
cost-sensitive, high-volume work. Current standard API rates per 1M tokens are
Sol `$5 / $0.50 / $6.25 / $30`, Terra
`$2.50 / $0.25 / $3.125 / $15`, and Luna
`$1 / $0.10 / $1.25 / $6` for uncached input / cached input / cache write /
output. OpenAI also recommends preserving the current reasoning effort as a
migration baseline and testing one level lower on representative work.

The requested research passes did not find a complete public benchmark that
compares all three GPT-5.6 tiers on SpecKit Pro's ten roles. Therefore this PRD
does not treat a marketing tier as a proven assignment. It defines an
evidence-first promotion process and ships only role assignments that clear a
consumer-focused quality floor.

## 2. Goals & Non-goals

### 2.1 Goals

- Give every installed SpecKit Pro Codex agent an explicit, role-appropriate
  model and reasoning-effort default selected by measured evidence.
- Preserve consumer-visible correctness, grounding, output contracts, and
  workflow completion while minimizing measured cost per successful run.
- Evaluate Sol, Terra, and Luna without forcing any tier into production when
  it fails the promotion bar.
- Make the model x effort decision reproducible through role fixtures,
  versioned results, and a documented promotion rule.
- Keep installation predictable: role-pinned defaults, one explicit global
  compatibility override, no silent downgrade, and complete verification of
  all ten installed agents.
- Rebuild and verify the Codex payload, active guidance, and installed-cache
  evidence before release.

### 2.2 Non-goals (out of scope)

- Changing Claude agent models, Claude commands, or Claude marketplace
  behavior.
- Adopting GPT-5.6 Pro mode, persisted reasoning, Programmatic Tool Calling,
  explicit prompt caching, or the Responses API multi-agent beta.
- Rewriting every agent prompt. Prompt cleanup is allowed only after an
  unchanged-prompt baseline and only when a before/after evaluation proves
  equal-or-better behavior with lower context cost or fixes a measured defect.
- Offering quality/balanced/economy install profiles or per-agent overrides in
  v1. The existing one-model compatibility override remains the KISS escape
  hatch.
- Claiming universal GPT-5.6 availability across accounts, operating systems,
  or Codex surfaces.
- Replacing historical model references, archived evidence, or old eval
  baselines solely to make repository-wide search results uniform.

## 3. Acceptance Criteria

### 3.1 Research Baseline and Candidate Matrix *(-> G56R-001)*

- **AC-1.1**: A dated research record inventories all ten Codex agents and every
  active source, installer, skill, validation, eval, generated-payload, and
  installed-cache surface that encodes their model or effort policy.
- **AC-1.2**: The record cites current official OpenAI pages for model IDs,
  positioning, pricing, context/tool support, Codex custom-agent fields, and
  reasoning-effort guidance; conflicting secondary claims are rejected or
  labeled unresolved.
- **AC-1.3**: Every agent has a current baseline, a primary GPT-5.6 candidate,
  at least one adjacent cheaper challenger where supported, an effort baseline,
  and a role-specific quality contract.
- **AC-1.4**: Facts, inferences, and unverified assumptions are visibly
  separated, and no public head-to-head benchmark is claimed where none was
  located.
- **AC-1.5**: The time-boxed spike ends with a go/no-go decision and fixture
  requirements for G56R-002; it does not change installed defaults.

### 3.2 Model-Effort Benchmark and Promotion Harness *(-> G56R-002)*

- **AC-2.1**: The Codex efficiency harness can run an explicit
  `model x model_reasoning_effort x agent` configuration instead of holding the
  TOML model constant, and it has a representative contract fixture for all ten
  agents.
- **AC-2.2**: Each result records the requested and returned model, effort,
  environment, wall time, input tokens, cached input, cache writes when exposed,
  output/reasoning tokens, actual Codex credits when exposed, and normalized
  cost using a dated official-pricing snapshot.
- **AC-2.3**: Deterministic contract, grounding/evidence, and safety checks are
  hard gates. Semantic quality uses a blinded role-specific rubric, with human
  review only for close or disputed outcomes.
- **AC-2.4**: Live evaluation is staged: three repeats per shortlisted
  configuration, expanded only when results are close or unstable, followed by
  installed-workflow UAT on the winners. Live runs are never part of the free
  default CI suite.
- **AC-2.5**: A configuration is promotable only with zero critical contract
  regressions and at least 95% of the current role-quality baseline. Among
  promotable configurations, the lowest measured cost per successful run wins;
  latency breaks ties.
- **AC-2.6**: Effort tuning starts with the current effort and one level lower.
  `max` is tested only for an unresolved quality-first failure, and no effort is
  committed until the installed Codex version accepts it for that model.
- **AC-2.7**: A versioned, replayable result artifact records candidates,
  failures, selected routes, rejected routes, pricing date, and promotion
  rationale.

### 3.3 Tier-aware Installer Defaults and Explicit Override *(-> G56R-003)*

- **AC-3.1**: A default install preserves each bundled agent TOML's validated
  role-specific model and effort instead of rewriting every non-helper agent to
  one default model.
- **AC-3.2**: The existing single global model override remains available as an
  explicit compatibility action and deliberately replaces all routed agent
  models only when the consumer requests it.
- **AC-3.3**: The installer never silently downgrades. Unsupported or
  unavailable requested models produce a clear, actionable report without a
  partial install or mutation of the bundled source templates.
- **AC-3.4**: Source and destination inventory agree on all ten agent TOMLs,
  including `uat-runbook-author.toml`; unrelated user agents are preserved.
- **AC-3.5**: Install output reports the effective model/effort matrix, the
  destination, override state, copied files, verification result, and restart
  requirement.
- **AC-3.6**: Implementation uses the post-XPLAT-009 Python runner/install path
  and does not restore a deleted active Bash helper.

### 3.4 Quality-critical Executor Routing *(-> G56R-004)*

- **AC-4.1**: `phase-executor`, `implement-executor`, and `analyze-executor`
  evaluate Sol at their current effort and one level lower, with Terra as the
  adjacent lower-cost challenger and `max` considered only after a measured
  quality failure.
- **AC-4.2**: Each committed model/effort clears the G56R-002 promotion rule on
  role-specific planning, TDD implementation, and analyze/remediation fixtures.
- **AC-4.3**: Agent sandbox, TDD, grounding, artifact, and remediation contracts
  remain unchanged unless a separately measured prompt cleanup is required.
- **AC-4.4**: Any prompt cleanup is evaluated after the routing baseline and is
  retained only when it preserves or improves quality while reducing context
  cost or fixing a specific regression.
- **AC-4.5**: Cohort-specific source, install, validation, and rollback evidence
  makes the route independently reviewable.

### 3.5 Structured-work Agent Routing *(-> G56R-005)*

- **AC-5.1**: `checklist-executor` and `uat-runbook-author` evaluate Terra at
  their current effort and one level lower, with Sol and Luna included only
  where the role fixture makes them credible adjacent candidates.
- **AC-5.2**: Checklist remediation remains complete at every severity and UAT
  runbooks remain executable, plain-English, non-circular, and traceable to
  acceptance criteria.
- **AC-5.3**: The selected routes clear the shared promotion rule and preserve
  workspace-write boundaries and fail-open/fail-closed behavior specific to
  each role.
- **AC-5.4**: Measured prompt cleanup follows the same baseline-first rule as
  G56R-004, and cohort-specific install and rollback evidence is recorded.

### 3.6 Read-only Reasoning Agent Routing *(-> G56R-006)*

- **AC-6.1**: `clarify-executor`, `domain-researcher`, `codebase-analyst`, and
  `spec-context-analyst` evaluate Terra as the primary candidate; Sol is a
  quality challenger for harder synthesis, and Luna is tested only for bounded
  scans where its output contract can be preserved.
- **AC-6.2**: The two current `xhigh` roles compare `xhigh` and `high`; the two
  current `low` analysts compare `low` and the next supported lower effort
  without relying on an omitted GPT-5.6 default.
- **AC-6.3**: All outputs remain grounded in their assigned evidence domain,
  preserve citations/file locators, and perform no writes.
- **AC-6.4**: The lowest-cost passing route is committed per agent; one cohort
  model is not forced across all four roles.
- **AC-6.5**: Measured prompt cleanup, install proof, and rollback evidence obey
  the same cohort contract as G56R-004.

### 3.7 Latency-first Helper Routing *(-> G56R-007)*

- **AC-7.1**: `autopilot-fast-helper` evaluates Luna at `low` and `none` when
  both are accepted by the installed Codex version, against its current Spark
  behavior and Terra as a fallback candidate.
- **AC-7.2**: The helper remains read-only, advisory, bounded to compression,
  triage, and query drafting, and never performs SpecKit reasoning or mutation.
- **AC-7.3**: The committed route clears the shared promotion rule and improves
  or preserves latency and cost per successful helper result; GPT-5.6 omission
  must not accidentally select its default `medium` effort.
- **AC-7.4**: Autopilot continues correctly when the helper is unavailable, and
  evidence wins over a requirement to use Luna.
- **AC-7.5**: Source, install, validation, prompt-cleanup, and rollback evidence
  is independently reviewable.

### 3.8 Payload, Documentation, UAT, and Release Proof *(-> G56R-008)*

- **AC-8.1**: The Codex payload is rebuilt from source; source TOMLs, generated
  payloads, manifests/checksums, install inventory, and expected model/effort
  matrix agree without hand-editing generated artifacts.
- **AC-8.2**: Active Codex install/autopilot guidance explains the selected
  routes, promotion evidence, explicit global override, restart requirement,
  and non-universal availability boundary without rewriting historical records.
- **AC-8.3**: Structural, installer, benchmark-replay, payload, installed-cache,
  default-suite, and active-path gates pass on the final source tree.
- **AC-8.4**: A live entitled Codex account completes at least one installed
  representative workflow per routed cohort, and the evidence records returned
  model, effort, quality result, latency, token/credit usage, and any safeguard
  intervention.
- **AC-8.5**: Release messaging makes only progressively proven claims and
  includes rollback through an explicit global override or previous plugin
  release.
- **AC-8.6**: The PR packet lists the final ten-agent matrix, rejected
  candidates, verification evidence, known availability gaps, and review order.

## 4. Migration Path (phased - one phase per SPEC)

- **Phase 1 (G56R-001) - Research baseline**: establish authoritative facts,
  current surfaces, candidate routes, and role contracts without changing
  defaults.
- **Phase 2 (G56R-002) - Benchmark foundation**: make model x effort evaluation,
  cost-per-success accounting, and layered promotion reproducible.
- **Phase 3 (G56R-003) - Installer policy**: preserve role-pinned defaults and
  keep one explicit global compatibility override on the Python runtime path.
- **Phase 4 (G56R-004 through G56R-007) - Role cohorts**: evaluate and migrate
  four independently reviewable cohorts in parallel after the shared contract
  is stable.
- **Phase 5 (G56R-008) - Release proof**: regenerate payloads, reconcile shared
  assertions, run installed UAT, and publish only proven claims.

## 5. Constraints

- Codex-only scope: `speckit-pro/codex-agents/`, Codex skills, the active Python
  runner/install path, Codex payloads, and directly related tests/evals/docs.
- G56R-003 and later implementation must ground on the post-XPLAT-009 active
  installer/runtime surface; no deleted Bash helper may be restored.
- Python 3.11+ standard library remains the installed runtime substrate; this
  PRD adds no runtime dependency.
- Agent TOMLs remain the role-policy source of truth. Generated payloads are
  rebuilt from source, never edited directly.
- `model_reasoning_effort` values must be accepted by the installed Codex
  version and selected model before they become defaults.
- No silent model fallback, partial install, or unreported change to an agent's
  sandbox/mutation boundary.
- Live AI evals remain developer-local and budgeted; deterministic and replay
  checks remain the default CI path.
- Release-please owns version changes; implementation does not manually bump
  plugin versions.
- Every implementation slice stays within the repository reviewability
  contract and reruns the forward size estimator when it becomes available.

## 6. Open Questions

- **OQ-1 (G56R-001):** Does the entitled release-test account expose all three
  GPT-5.6 tiers and every candidate effort through the installed Codex client?
  Recommendation: record capability probes and abstain from unverified routes.
- **OQ-2 (G56R-002):** Does current Codex telemetry expose cache-write tokens and
  actual credit usage separately? Recommendation: record native fields when
  present and use dated API-rate normalization as a clearly labeled fallback.
- **OQ-3 (G56R-003):** Which Python helper owns agent installation after
  XPLAT-009 merges? Recommendation: bind to the live authoritative registry at
  scaffold time instead of naming a removed compatibility script.
- **OQ-4 (G56R-004 through G56R-007):** Which adjacent-tier challengers survive
  the research spike's availability and contract screen? Recommendation: keep
  the approved shortlist narrow and expand only unstable comparisons.

## 7. SPEC Catalog Crosswalk

| Feature (§3) | Acceptance Criteria | SPEC | Depends on | Priority |
|---|---|---|---|---|
| Research Baseline and Candidate Matrix | AC-1.* | G56R-001 | - | P1 |
| Model-Effort Benchmark and Promotion Harness | AC-2.* | G56R-002 | G56R-001 | P1 |
| Tier-aware Installer Defaults and Explicit Override | AC-3.* | G56R-003 | G56R-002; XPLAT-009 runtime stable | P1 |
| Quality-critical Executor Routing | AC-4.* | G56R-004 | G56R-003 | P1 |
| Structured-work Agent Routing | AC-5.* | G56R-005 | G56R-003 | P1 |
| Read-only Reasoning Agent Routing | AC-6.* | G56R-006 | G56R-003 | P1 |
| Latency-first Helper Routing | AC-7.* | G56R-007 | G56R-003 | P1 |
| Payload, Documentation, UAT, and Release Proof | AC-8.* | G56R-008 | G56R-004 through G56R-007 | P1 |

## 8. Success Criteria

1. All eight Features map 1:1 to G56R-001 through G56R-008 and all acceptance
   criteria are traceable through roadmap, implementation, and release evidence.
2. Every shipped agent route has zero critical contract regressions, at least
   95% of its current quality baseline, and the lowest measured cost per
   successful run among passing candidates, with latency used as tie-breaker.
3. A clean install verifies all ten agents and reports the exact effective
   model/effort matrix with no silent fallback.
4. Source, generated Codex payload, installed cache, guidance, tests, and UAT
   evidence agree on the final matrix.
5. Consumers retain a documented global compatibility override and a previous
   release rollback path.

## 9. References

- **Technical roadmap:** [codex-gpt-5-6-agent-routing-technical-roadmap.md](ai/specs/codex-gpt-5-6-agent-routing-technical-roadmap.md)
- **Roadmap MOC:** [codex-gpt-5-6-agent-routing-roadmap-MOC.md](ai/specs/codex-gpt-5-6-agent-routing-roadmap-MOC.md)
- **Constitution:** [Racecraft Plugins Public Constitution](../.specify/memory/constitution.md)
- **Project standards:** [AGENTS.md](../AGENTS.md) and [CLAUDE.md](../CLAUDE.md)
- **Latest-model guidance:** [Using GPT-5.6](https://developers.openai.com/api/docs/guides/latest-model)
- **Migration guidance:** [Upgrading to GPT-5.6 Sol](https://developers.openai.com/api/docs/guides/upgrading-to-gpt-5p6-sol)
- **Codex subagents:** [Choosing models and reasoning](https://developers.openai.com/codex/concepts/subagents#choosing-models-and-reasoning)
- **Model pages:** [Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol), [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna)
- **Pricing:** [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)
- **Prompt guidance:** [GPT-5.6 prompting best practices](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices)

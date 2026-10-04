# typesafe-jev as a decision model for Spec Kit command selection

> Status: research complete, 2026-10-04. Resolves #1148 on the planning
> performance map (#1144). Plugin versions: speckit-pro 2.40.0, typesafe-jev
> 0.9.2 (binary 0.9.2). Model that answered: `jev-1.13.0`.
> Dated record: code citations describe the tree at commit `f7c97c1af`.

## Answer

Jev is cheap and fast enough for any plan-stage routing judgment. Cost and
latency are not the constraint. Accuracy, privacy and fail-safe behavior are.

| Judgment | Fit | Why |
| --- | --- | --- |
| Consensus tier per clarify item | **Good fit** | It separated evidence-backed items (accept, p 0.76 to 0.88), security items (full consensus, p 0.96 to 0.99) and open defaults (split, confidence about 0.3). It kept a docs item that only *mentions* audits out of the security route (noul 0.08). Stable across repeats and option order. |
| Which checklist domains | **Good fit for API and service specs, weak fit elsewhere** | On the webhook spec it picked exactly the 4 domains a reviewer would (all p ≥ 0.89, the rest ≤ 0.47). On a CLI tooling spec and a docs-only spec it found almost nothing, because the domain catalog describes web-app risks. Use it to add domains, never to drop mandatory ones. |
| Run or skip clarify | **Weak fit** | It said "run clarify" for all three specs (p 0.69 to 0.88). It does not discriminate, so it would skip almost nothing. The ambiguity score (1.4 to 2.1 of 3) carries more signal and could set the number of sessions instead. |
| Planning path (shorter or full) | **No fit as one question** | It chose "full" for all three, including a docs-only spec (p 0.60). The answer mostly restates the option text. Compute the path in code from separate size, security and ambiguity answers instead. |

Two conditions apply to every judgment:

- **Only with spec text.** With derived features only (counts and keyword hits),
  domain and security answers collapsed toward 0.5 and the planning-path answer
  became falsely certain. Redacting to features does not work. Private repos
  would send spec text to TypeSafe, or to OpenRouter on fallback.
- **Call the binary from the runner, not the MCP tool from the agent.** An
  agent-side call costs an orchestrator turn (about 171K input tokens) to save a
  judgment that costs under a cent. The runner already calls the binary for the
  research broker.

## Context

The plan stage runs specify, 3 clarify sessions, plan, checklist domains, tasks
and analyze, with a consensus layer (3 analysts plus a synthesizer per round).
The map asks whether Jev could make four routing judgments: run or skip
clarify, which checklist domains, the consensus tier per clarify item, and the
planning path (upstream Spec Kit v1.1.0 documents a shorter path: specify,
plan, tasks, implement, converge).

This repo already has a design frame for this. The typed-judgment catalog
([harness-engineering-uplift-jev-catalog.md](../specs/harness-engineering-uplift-jev-catalog.md))
lists JEV-017 (marker-free ambiguity detection), JEV-021 (checklist-domain
applicability) and JEV-026 (consensus evidence-domain routing). All three are
deferred. They depend on HRNS-024 (shared typed-decision contract, status
Pending and Frozen), HRNS-025 (run journal) and HRNS-027 (dual-host Jev
adapter). The catalog's defaults apply to anything this note recommends: off
until per-project activation, shadow mode first, data consent before every
outbound request, a missing judgment is `unknown` and never success, mandatory
domains stay mandatory, and Jev is never a consensus vote.

## Method

All live calls used public inputs from this repository. Nothing from a private
repo or private fixture was sent.

**Specs.** Only one folder under `specs/` has a `spec.md`
(`formal-001-selective-formal-methods`; `brand-001` has only a map of content).
Two public test fixtures in this repo filled the other sizes:

| Id | Source | Lines | Words | Stories | Requirements | Character |
| --- | --- | --- | --- | --- | --- | --- |
| S-webhook | `tests/speckit-pro/layer3-functional/fixtures/headless/coach-webhook-project/spec.md` | 36 | 248 | 1 | 5 | HTTP service with HMAC signatures and retries |
| M-formal-001 | `specs/formal-001-selective-formal-methods/spec.md` | 83 | 671 | 5 | 14 | CLI and workflow tooling, two hosts, checkers |
| L-doc-008 | `tests/speckit-pro/layer6-integration/performance-fixtures/troubleshooting-security/source/spec.md` | 156 | 3,071 | 3 | 19 | Docs-only pages about troubleshooting, security and rollback |

Counts are the derived features below. None of the three has a
`[NEEDS CLARIFICATION]` marker.

**Calls.** 28 live calls in total, well under the 60 budget:

- 25 through `evaluate call --plugin-defaults`, with the same environment the
  research broker sets (`JEV_PROVIDER=typesafe`, `JEV_FALLBACK_PROVIDER=openrouter`,
  `JEV_REQUEST_TIMEOUT=45s`). Timed from process start to exit.
- 2 with `JEV_PROVIDER=openrouter`, to see which response fields that backend
  sends.
- 1 through the MCP tool `evaluate`, to confirm the agent path gives the same
  answers. It did (tier 0.97 versus 0.96 to 0.99; noul 0.04 versus 0.04).

**Expected labels** in the results below are the author's own judgment, written
before reading the answers. They are not a labelled set. A real calibration
needs one (see Open questions).

## State shapes

Three shapes. Field names are what the questions point at.

**Plan judgments, text plus features** (`plan_text`):

```json
{"feature": {
  "spec_text": "<the whole spec.md>",
  "derived": {
    "spec_lines": 83, "spec_words": 671,
    "needs_clarification_markers": 0,
    "user_story_count": 5, "functional_requirement_count": 14,
    "acceptance_scenario_count": 0,
    "has_scope_or_non_goals_section": true, "has_edge_cases_section": false,
    "domain_keyword_hits": {"security": 3, "error-handling": 3, "...": "one count per domain"}
  }}}
```

**Plan judgments, features only** (`plan_feat`): the same object with
`spec_text` removed. This is the privacy variant.

**Consensus tier** (`tier`): the clarify items only, no spec text.

```json
{"items": [
  {"question": "...", "recommended_answer": "...", "evidence": "..."}
]}
```

`derived` is computed in code with regular expressions (counts and keyword hits
per checklist domain). Jev's own docs say to keep counting in code, so the
counts are inputs, not questions.

The clarify items were written by the author from each spec, three per spec:
one settled by cited text, one where the spec is silent, and one touching
security or a security word. They imitate a clarify executor's output; they are
not real executor output.

| Spec | Item | Recommended answer | Cited evidence |
| --- | --- | --- | --- |
| S | What HTTP status should POST /deliveries return for a repeated event ID? | HTTP 202 with the existing delivery ID. | Requirements: a successful request returns a delivery ID and HTTP 202; repeated submissions of the same event ID return the existing delivery ID. |
| S | Should retries add random jitter to the 1, 5, 30 and 120 minute waits? | No. Use the fixed schedule exactly as written. | Requirements: attempts after the first wait 1, 5, 30, and 120 minutes respectively. |
| S | How is the subscription secret stored at rest, and may it appear in logs? | Store it encrypted with the platform key service and never write it to logs. | Requirements: GET /deliveries/{id} must not expose the subscription secret. Storage and logging are not stated. |
| M | Which Apalache version should qualification target? | Apalache 0.62.2. | FR5: Qualify Apalache 0.62.2 and TLC 1.7.4 by actual execution before claiming compatibility. |
| M | Should a missing legacy formal-methods selection be treated as disabled or as an error? | Treat it as disabled. | FR2: A missing legacy selection is disabled. Malformed selection fails closed. |
| M | What default time budget should one TLC model check have? | Ten minutes per check, overridable in the catalog. | FR3 says the catalog records budgets. No default value is stated anywhere in the specification. |
| L | Should the troubleshooting page offer a button that runs the diagnostic command? | No. Show copyable commands or file paths only. | User Story 1, scenario 3: the page presents copyable commands or file paths only and does not execute local commands. |
| L | Should the security and trust page say the plugin has been security audited or certified? | No. State that the page is user documentation, not an audit, certification or control attestation. | User Story 2, scenario 3: DOC-008 is user documentation, not a security audit, certification, threat model, or control attestation. |
| L | Which rollback reference should the page recommend first: a version tag, a commit SHA, or a marketplace source pin? | A version tag. | User Story 3, scenario 3 lists a known marketplace source, generated payload, version, or commit reference, without ranking them. |

## Questions asked (verbatim)

Question ids are not sent to the model. Only `instructions` and `criteria` are.

### Plan batch (20 questions in one call)

**`clarify_needed`** (noul)

- instructions: "Decide whether running a clarification session on this feature specification is likely to change the plan. Judge only from `feature`. Answer yes when the specification leaves at least one decision open that would change the design, scope, data model, interfaces, or acceptance tests, and a reasonable planner could not settle it from the text alone."
- true: "At least one open decision materially changes the plan: an unstated behavior, a missing limit or error rule, a conflict between requirements, or an undefined term that a planner must guess."
- false: "Every decision a planner needs is stated or follows directly from the text; any remaining gaps are cosmetic or have an obvious default."

**`ambiguity_level`** (score)

- instructions: "Rate how much material ambiguity remains in the specification in `feature` for a planner who must start design now."
- levels:
  0. "None: requirements, limits, error behavior and scope are all stated; a planner would ask no questions."
  1. "Minor: one or two small gaps with an obvious default, such as wording or a log format."
  2. "Moderate: a few gaps where a planner must choose between reasonable designs, such as a missing limit, an unstated error rule, or an undefined term."
  3. "Major: core behavior, scope or interfaces are undecided, or requirements conflict, so planning would rest on guesses."

**`planning_path`** (choice)

- instructions: "Choose the planning path for this feature, judging only from `feature`."
- `shorter`: "Shorter path (specify, plan, tasks): the feature is small and self-contained, the specification is complete, it touches few files, and it carries no security, data-migration or cross-host risk."
- `full`: "Full path (specify, clarify, plan, checklists, tasks, analyze): the feature is large, spans several subsystems or hosts, has open questions, or carries security, data, or compatibility risk."
- `none_fits`: "Neither description fits, or the specification is too incomplete to tell."

**`size_class`** (score)

- instructions: "Estimate how large the implementation of the feature in `feature` will be."
- levels:
  0. "Tiny: one file or a configuration change, under about 100 changed lines."
  1. "Small: a single module or command, a few files, under about 500 changed lines."
  2. "Medium: several modules or one subsystem end to end, roughly 500 to 2,000 changed lines."
  3. "Large: several subsystems or both hosts, more than about 2,000 changed lines or several pull requests."

**`security_sensitive`** (noul)

- instructions: "Decide whether the feature in `feature` ships code that itself handles credentials, secrets, authentication, authorization, signatures, or personal data."
- true: "The feature's own deliverable verifies, stores, transmits or decides on credentials, secrets, signatures, access rights or personal data."
- false: "The feature does none of that itself; it may describe or mention such topics, for example in documentation, without handling them in code."

**`domain_<d>`** (15 nouls, one per checklist domain), from this template:

- instructions: "Decide whether a requirements-quality checklist for the `<d>` domain would find real gaps in the specification in `feature`. Answer yes only when the feature's own deliverable includes `<signals>`, not when the text merely mentions these words."
- true: "The feature builds or changes `<signals>` as part of its deliverable."
- false: "The feature does not build or change `<signals>`, or only mentions them in passing or in documentation about them."

`<d>` and `<signals>` come from the signal table in
`speckit-pro/skills/speckit-coach/references/checklist-domains-guide.md`:

| Domain | Signals |
| --- | --- |
| api-contracts | API endpoints, REST routes, request or response schemas, HTTP methods |
| ux | user-facing UI, components, layouts, interactions, forms |
| accessibility | keyboard navigation, screen readers, ARIA, color contrast, WCAG |
| security | authentication, authorization, tokens, secrets, user roles, input validation |
| performance | response time budgets, caching, bundle size, query performance, concurrency |
| data-integrity | database schemas, migrations, validation rules, data consistency, transactions |
| llm-integration | LLM prompts, model calls, token limits, streaming, extraction, embeddings |
| streaming-protocol | SSE, WebSocket, streaming protocols, real-time updates, event formats |
| error-handling | error handling, retry logic, fallbacks, circuit breakers, degradation |
| state-management | state management, session handling, conversation history, caching strategy |
| integration | third-party APIs, external services, webhooks, data imports |
| mobile-ux | touch targets, gestures, orientation, offline, responsive breakpoints |
| reliability | logging, monitoring, alerting, health checks, observability |
| privacy | personal data, consent, retention periods, deletion, data export |
| supply-chain | new third-party packages, dependency upgrades, vendored code, build or install scripts |

### Tier batch (6 questions in one call, per spec)

For each item `i` in 0 to 2:

**`tier_i`** (choice)

- instructions: "Decide how the clarification item in `items[i]` should be settled. The item has a question, the executor's recommended answer, and the evidence it cites."
- `accept`: "Accept the recommended answer as is: the cited evidence settles the question, the answer is cheap to reverse, and no reasonable reviewer would choose differently."
- `single_analyst`: "Ask one analyst to check: the answer is probably right, but it rests on one assumption that a quick look at the code or specification would confirm."
- `full_consensus`: "Run full three-analyst consensus: reasonable reviewers could choose differently, the answer is costly to reverse, or it touches security, credentials, access control or personal data."
- `none_fits`: "The item is malformed, the question cannot be answered, or none of these fits."

The `tier_rev` run sends the same four options in reverse order, because Jev's
docs warn that `jev-1.13` leans toward the first option.

**`security_i`** (noul)

- instructions: "Decide whether the question in `items[i]` is about security: credentials, secrets, access control, signatures, or personal data handled by the feature."
- true: "The answer changes how the feature protects or handles credentials, secrets, access, signatures or personal data."
- false: "The answer does not change any protection; security words, if present, are used in passing or about documentation."

### Single-question latency probe

`clarify_needed` alone, over the `plan_text` state.

## Results

### Plan batch, text plus features (first run)

| Question | S-webhook | M-formal-001 | L-doc-008 | Author's expectation |
| --- | --- | --- | --- | --- |
| clarify_needed | 0.87 | 0.88 | 0.69 | S yes (secret storage, payload limits unstated); M yes (terse); L borderline |
| ambiguity_level (0 to 3) | 1.90 (conf 0.88) | 2.14 (conf 0.76) | 1.43 (conf 0.48) | S 1 to 2, M 2, L 1 |
| planning_path | full 0.77, shorter 0.22 | full 1.00 | full 0.60, shorter 0.38 | S either, M full, L shorter |
| size_class (0 to 3) | 1.82 (conf 0.81) | 2.99 (conf 0.99) | 1.52 (conf 0.48) | S 1, M 3, L 1 |
| security_sensitive | 0.95 | 0.21 | 0.03 | S yes, M no, L no |
| domain_api-contracts | **0.93** | 0.06 | 0.06 | S yes |
| domain_security | **0.89** | 0.11 | 0.05 | S yes |
| domain_error-handling | **0.90** | 0.53 | 0.06 | S yes, M yes |
| domain_integration | **0.90** | 0.21 | 0.05 | S yes, M yes (checkers, gh-stack) |
| domain_state-management | 0.47 | 0.38 | 0.05 | M yes (checkpoints, resume) |
| domain_data-integrity | 0.26 | 0.10 | 0.04 | S maybe (idempotency) |
| domain_supply-chain | 0.05 | 0.20 | 0.04 | M yes (pinned checker versions, no implicit install) |
| domain_ux | 0.04 | 0.11 | 0.25 | L maybe (doc pages) |
| domain_reliability | 0.14 | 0.17 | 0.04 | none |
| domain_performance | 0.14 | 0.15 | 0.05 | none |
| domain_privacy | 0.07 | 0.05 | 0.04 | none |
| domain_accessibility | 0.04 | 0.05 | 0.05 | none |
| domain_llm-integration | 0.04 | 0.07 | 0.04 | none |
| domain_streaming-protocol | 0.05 | 0.05 | 0.03 | none |
| domain_mobile-ux | 0.04 | 0.06 | 0.04 | none |

Reading:

- **S-webhook domains** match the expectation exactly at a 0.5 threshold: 4
  domains, inside the guide's target of 2 to 4.
- **M-formal-001 domains** catch error-handling (0.53) and miss integration,
  state-management and supply-chain. The catalog's signals are web-app words;
  a CLI that pins checker versions does not read as "supply-chain" to a literal
  model. Jev's docs name literal reading as failure mode 1.
- **L-doc-008 domains** are all at or below 0.25. That follows the question as
  written ("only when the deliverable builds it"). A docs feature needs domains
  the catalog does not have (claim accuracy, source citations).
- **clarify_needed** is high everywhere. As a skip gate it would skip nothing.
- **planning_path** always says full. For S it follows the option's own rule
  ("carries security risk"). For L, a docs-only change, it leans full at 0.60.

### Plan batch, features only (privacy variant)

| Question | S text | S features | M text | M features | L text | L features |
| --- | --- | --- | --- | --- | --- | --- |
| clarify_needed | 0.87 | 0.86 | 0.88 | 0.85 | 0.69 | 0.82 |
| ambiguity_level | 1.90 | 2.29 | 2.14 | 2.04 | 1.43 | 2.11 |
| planning_path (full) | 0.77 | 0.79 | 1.00 | 1.00 | 0.60 | **1.00** |
| size_class | 1.82 | 1.37 | 2.99 | 1.91 | 1.52 | 2.45 |
| security_sensitive | 0.95 | **0.48** | 0.21 | **0.50** | 0.03 | **0.54** |
| domain_api-contracts | 0.93 | **0.30** | 0.06 | 0.18 | 0.06 | 0.26 |
| domain_security | 0.89 | **0.24** | 0.11 | 0.25 | 0.05 | 0.32 |
| domain_error-handling | 0.90 | **0.32** | 0.53 | 0.47 | 0.06 | 0.47 |
| domain_integration | 0.90 | **0.34** | 0.21 | 0.31 | 0.05 | 0.25 |
| domain_mobile-ux | 0.04 | 0.14 | 0.06 | 0.12 | 0.04 | **0.41** |

Without text, every domain and security answer moved into the 0.1 to 0.55 band.
No domain crossed 0.5 on any spec. `security_sensitive` sat at 0.48 to 0.54,
which means "unknown". The planning path for the docs spec went from an honest
0.60 to a false 1.00. Size flipped order: L-doc-008 rated larger than
M-formal-001. Features only is not a usable redaction for these judgments.

### Tier batch

| Item | Expected | tier (forward order) | tier (reversed order) | security noul |
| --- | --- | --- | --- | --- |
| S0 status for repeated event ID | accept | accept 0.76 (conf 0.69) | accept 0.84 | 0.03 |
| S1 jitter on retry waits | accept or single | accept 0.62 (conf 0.50), single 0.20 | accept 0.62 | 0.04 |
| S2 secret storage and logging | full consensus | full 0.99 (conf 0.97) | full 0.96 | 0.98 |
| M0 Apalache version | accept | accept 0.88 (conf 0.84) | accept 0.85 | 0.02 |
| M1 missing legacy selection | accept | accept 0.87 (conf 0.84) | accept 0.87 | 0.06 |
| M2 default TLC budget (not stated) | single or full | single 0.49, full 0.39 (conf 0.31) | single 0.47, full 0.39 | 0.02 |
| L0 run-command button | accept | accept 0.77 (conf 0.70) | accept 0.76 | 0.17 |
| L1 "audited or certified" claim | accept | accept 0.78 (conf 0.71) | accept 0.79 | 0.08 |
| L2 rollback reference order | single or full | single 0.49, full 0.31 (conf 0.32) | single 0.51, full 0.28 | 0.06 |

All nine choices held when the option order was reversed. The two items where
the spec is silent came back with confidence near 0.3. That is the signal a
confidence gate needs: route low-confidence items to consensus, accept
high-confidence ones.

Item L1 matters for the current protocol. The consensus protocol routes any
item containing a security keyword to all three analysts
(`skills/speckit-autopilot/references/consensus-protocol.md`, Security
Keywords). Jev scored L1's security noul at 0.08. A Jev gate could avoid that
over-routing, but only where the protocol already allows it: the keyword rule is
a contract, and JEV-026's authority boundary forbids bypassing mandated rounds
without a reviewed routing-contract change.

### Stability (identical repeated calls)

| Request | Runs | Largest noul or score spread | Choice changed? |
| --- | --- | --- | --- |
| plan_text M-formal-001 (20 questions) | 5 | 0.10 (domain_state-management 0.38 to 0.48); all others ≤ 0.07 | No (full 1.00 every run) |
| plan_text L-doc-008 (20 questions) | 3 | 0.06 (size_class 1.49 to 1.55) | No (full 0.60 to 0.61) |
| plan_feat M-formal-001 (20 questions) | 3 | 0.08 (ambiguity_level 2.04 to 2.12) | No |
| tier S-webhook (6 questions) | 3 + 1 OpenRouter + 1 MCP | 0.11 on tier_0's top probability (0.76 to 0.87) | No |

Answers are not bit-identical between calls. Replay must compare within a
tolerance, or treat the logged answer as the record. A threshold set near a
value that wobbles by 0.1 (state-management at 0.38 to 0.48 against 0.5) will
flip.

### Latency

| Path | Calls | Wall clock |
| --- | --- | --- |
| Binary, TypeSafe, all requests | 25 | median 0.225 s, range 0.187 to 0.313 s |
| Binary, 20-question batch | 14 | median 0.249 s |
| Binary, 1 question | 3 | median 0.278 s |
| Binary, OpenRouter backend | 2 | 0.243 and 0.341 s |
| MCP tool from the agent | 1 | not timed; the agent turn around it dominates |

Times include process start and key-file reads. A 20-question batch is no slower
than one question, which matches TypeSafe's statement that Jev reads the state
once and answers every question in parallel
([Models](https://docs.typesafe.ai/models.md)). The tool description's claim of
70 to 500 ms per call holds.

### Cost

TypeSafe prices `jev-1.13.0` at **$0.042 per million input tokens; output tokens
are free** ([Models](https://docs.typesafe.ai/models.md), read 2026-10-04). The
OpenRouter replies carried `usage.cost`, which matched that rate (1,448 tokens
cost $0.0000608).

| Request | Input tokens | Cost |
| --- | --- | --- |
| One noul, S spec | 998 | $0.00004 |
| 6-question tier batch | about 1,450 | $0.00006 |
| 20-question plan batch, L spec with full text | 8,638 | $0.00036 |
| All 25 binary calls in this study | 88,769 | $0.0037 |

One orchestrator turn at the measured 171K-token median context, on Claude
Sonnet 5.5 (prices from the claude-api skill's model table, cached 2026-09-25:
$2.00 per million input tokens, cache reads $0.20, 5-minute cache writes at
1.25 times input):

- with no caching: 171K × $2.00 = **$0.34** per turn, input only;
- at the measured run-wide 94% cache-read share: about 161K × $0.20 + 10K ×
  $2.00 to $2.50 = **about $0.05 to $0.06** per turn, input only.

The largest Jev batch costs about 1/150 of a cached orchestrator turn and about
1/950 of an uncached one. The Jev call is never the cost. What it saves (a
skipped clarify session, a skipped checklist domain, a narrower consensus round)
is several agent turns each. What it can waste is an orchestrator turn spent
issuing it, which is why the runner, not the agent, should make the call.

## Auditability

What the runner must log per decision, for the decisions list and for replay:

| Field | Source | Present in the reply? |
| --- | --- | --- |
| Question set id and version (hash of the canonical question JSON) | runner | No, compute it |
| Question text | runner | No; ids are not sent to the model, so store the full text or the hash plus the versioned file |
| State digest (SHA-256 of canonical JSON) | runner | No, compute it. This study used a 16-hex prefix per state |
| Which inputs fed the state (spec path and blob SHA) | runner | No |
| Model id | reply `model` | **Yes.** TypeSafe sends `jev-1.13.0`; OpenRouter sends `typesafe/jev-1.13-20260917` |
| Backend that answered | inferred | **Not directly.** TypeSafe's reply has no backend field. OpenRouter's reply adds `provider: "TypeSafe"` and an `id`. The binary prints a one-time fallback notice on stderr only. The research broker infers the backend from the model id's shape (`research_broker.py`, `interpret_jev_response`). |
| Answers with probabilities and confidence | reply `answers` | Yes on TypeSafe. On OpenRouter, `confidence` and `probabilities` are optional for choice and score (`typesafe-jev/docs/provider-contracts.md`); both calls here included them |
| Usage and cost | reply `usage` | Tokens on both; `cost` on OpenRouter only |
| Threshold policy id and the routing decision taken | runner | No |
| Exit code and latency | runner | No |

Two replay rules follow from the data:

- Pin the model. `jev-latest` is an alias that moves when TypeSafe ships a new
  release, and TypeSafe advises pinning a versioned id once thresholds are tuned
  ([Models](https://docs.typesafe.ai/models.md), Aliases). The research broker
  already keys its thresholds to the `jev-1.13` family and marks other answers
  `unpinned_model` (`research-broker-contract.md`). #1124 replaces that with a
  per-model threshold table; routing thresholds belong in the same table.
- Replay is approximate. Repeats differ by up to 0.11. Replay should re-run and
  check the decision is unchanged, or read the logged answer.

#1119 already plans a `screening` object that names the answering backend and
model in each broker envelope. A routing caller needs the same field, which
argues for the binary's `call` output naming the backend rather than each
caller inferring it.

## Privacy

**What leaves the machine.** The `state` and `questions` of each call, over
HTTPS, and nothing else: no telemetry, no logging of request contents
(`typesafe-jev/SECURITY.md`, "What this tool does with your data"). For these
judgments the state is the spec text and the clarify items, which for a
private repo are private product requirements.

**To whom.**

- **TypeSafe** (`api.typesafe.ai`), the primary. The Privacy Policy (last
  updated 2025-11-19) says TypeSafe will not train or fine-tune models on Input
  and will not disclose Input to third parties other than its service
  providers. Retention: "as long as reasonably necessary to provide you with
  the Services, or otherwise in support of our business or commercial
  purposes". The Data Processing Agreement (last updated 2026-04-24) says the
  same in DPA terms and lists subprocessors on TypeSafe's trust page. Zero data
  retention is offered to enterprise customers only
  ([Legal](https://docs.typesafe.ai/legal.md)). No fixed retention period is
  published for other accounts.
- **OpenRouter** (`openrouter.ai`), the fallback in both plugin MCP files and in
  the broker's `JEV_PLUGIN_SETTINGS`. OpenRouter stores prompts only if the
  account opts in, stores request metadata (token counts, latency), and samples
  a small number of prompts for anonymous categorization
  ([Data Collection](https://openrouter.ai/docs/guides/privacy/data-collection.md)).
  It then forwards to TypeSafe as the provider (`provider: "TypeSafe"` in the
  replies), so TypeSafe's terms apply too.

**Can the runner send only derived features?** Tested above: no. Features keep
`clarify_needed` roughly where text put it, but that judgment was already
non-discriminating. Domains, security and size lose their signal. Untested
middle grounds: sending only the requirement lines, or only the clarify items
(the tier batch already sends no spec text, only the item question, the
recommended answer and the quoted evidence).

**Implication for private repos.** Routing on Jev means sending spec content to
an external provider on every planning run. The catalog's default already says
data consent is required before every outbound request, with data classes and
provider named. That consent must be per project, and the default must be off.

## Availability and integration

**Broker failure history.** Every research-broker call failed in both measured
canary runs (#1152 counts 24 and 27 calls). The local transcripts of the two
Claude Code canary runs that made broker calls were checked here. They were
read locally, never sent anywhere, and are reported as categories only. That
these two runs are the same two #1152 measured is likely but not confirmed.

- `screening_mode` was `jev` in every envelope. Jev was configured and healthy.
- Every `docs_query` failure was `fetch_failed` with reason `rate_limited`, which
  the broker raises for HTTP 429, 432 or 433 from the provider
  (`research_broker.py`, `_status_code`). `docs_query` goes to Context7, which
  ran keyless.
- Every `research_search` returned `search_unavailable`: no Tavily key was
  configured.
- No `jev_*` drop reason (`jev_unscreened`, `jev_credential_unusable` and so on)
  appeared in either run.

So the broker's failures were Context7 rate limits and an absent Tavily key, not
Jev. In this study, 28 of 28 Jev calls answered, and none fell back.

**Rate limits.** TypeSafe lists 100K tokens per second and 80 requests per
second, and warns the limits "are adjusting dynamically" under demand
([Models](https://docs.typesafe.ai/models.md)). A plan stage needs a handful of
calls, so this is far from the limit, but a 429 is possible and the binary
retries 429 and 529 on TypeSafe (`typesafe-jev/cmd/evaluate/config.go`).

**Fail-safe direction.** Routing must fail **open to the full path**, the
current behavior. That is the opposite of the broker's TS4 rule, which fails
closed. For the broker, an unscreened chunk is the risk. For routing, a skipped
phase is the risk, and running every phase is the safe default. Any exit other
than 0 from `evaluate call` (2 to 6) should mean "no judgment", recorded as
`unknown`, and the plan stage runs as today.

**How each host would call it.**

| Path | How | Cost per call | Host notes |
| --- | --- | --- | --- |
| Runner calls the binary (recommended) | A runner helper sends JSON to `evaluate call --plugin-defaults` on stdin and reads exit codes 0 to 6, as `ResearchBroker._evaluate` does. Resolve the binary and environment through `research_preflight.resolve_binary` and `jev_child_environment`, so the #1122 rename (`racecraft-decide`, `DECIDE_*`) changes one place. | No agent tokens | Same code on both hosts. Keys come from key files under `HOME`, so no environment forwarding is needed. **Unconfirmed:** whether a runner helper launched from Codex's shell tool can reach the network. Codex defaults to no network access in its sandbox (OpenAI's approvals and security docs, cited in `docs/prd-interactive-documentation.md`). The research broker avoids this because Codex launches it as an MCP server. |
| Agent calls the MCP tool | The orchestrator calls `evaluate` and reads the answer. | One orchestrator turn, about 171K input tokens | The answer sits in the agent's context, unlogged unless the agent copies it. On Codex, the typesafe-jev MCP entry declares no `env_vars`, so a key set only as an environment variable may not reach the server; key files work. This is the same gap #1121 fixes for the research broker. |
| Through the research broker | Add a routing tool to the broker MCP server. | One agent turn to call it | Reuses the broker's preflight, but mixes routing with web research screening, and the broker is the component that failed in the canary. |

**Related tickets.** #1120 (re-probe) and #1124 (backend chain and per-model
thresholds) apply to any routing caller as written. #1124's chain also means the
answering model may be Cloudflare Clef, which has no calibration yet (#1125).
Routing thresholds would need their own calibration per model family, separate
from the broker's hazard thresholds.

## Recommendations for the map

1. **Do not let Jev choose the planning path or skip clarify.** Set the path
   from deterministic signals plus an owner rule, and keep clarify. If a skip
   rule is wanted, gate it on the ambiguity score and on zero
   `[NEEDS CLARIFICATION]` markers, and measure it in shadow first.
2. **If the consensus tier is adopted, use Jev there first.** Accept when the
   choice is `accept` with confidence at or above a calibrated cut and the
   security noul is low. Send everything else to the current protocol. Keep the
   security keyword rule unless the routing contract is changed on purpose.
3. **Use domain nouls to add checklist domains, never to remove mandatory
   ones.** Extend the catalog descriptions for CLI, tooling and docs features
   before trusting low scores there.
4. **Run it from the runner, in shadow, behind per-project consent.** Fail open
   to the full path. Log the fields in the audit table.
5. **Build on the existing foundation.** These are JEV-017, JEV-021 and JEV-026
   in the catalog, which wait on HRNS-024, HRNS-025 and HRNS-027. A
   performance ticket that needs routing sooner would have to jump that
   queue; that is a sequencing decision for the map.

## Open questions and what I could not confirm

- **Accuracy at scale.** Three specs and nine items, with the author's labels.
  A real threshold needs a labelled set: past SPECs with their actual clarify
  outcomes, chosen domains and consensus results. Not available publicly.
  Looked in: `specs/`, the test fixtures, the catalog.
- **Codex runner network access.** Not tested. Whether a runner helper invoked
  through Codex's shell tool can reach `api.typesafe.ai` depends on the
  sandbox's network setting. Needs a real Codex run.
- **Agent-path latency.** The MCP call was not timed. The orchestrator turn
  around it dominates, and no Codex plan-stage profile exists yet (#1079).
- **TypeSafe retention period.** The DPA and Privacy Policy give no fixed
  period. Looked in: TypeSafe Legal, DPA, Privacy Policy (all read
  2026-10-04).
- **OpenRouter omitting probabilities.** The docs allow it; both OpenRouter
  calls here included them. Not observed, not ruled out.
- **Orchestrator turn cost** uses the run-wide 94% cache-read share as a
  per-turn estimate. Per-turn cache splits were not measured, and subscription
  billing is not per token, so the dollar figures are list-price equivalents.
- **Canary broker counts.** The transcript grep counted envelope strings, which
  appear more than once per call. Only the categories (Context7 rate limit,
  Tavily absent, no Jev reason) are reported, not exact per-call counts.

## Sources

- TypeSafe docs: [documentation index](https://docs.typesafe.ai/llms.txt),
  [Models](https://docs.typesafe.ai/models.md) (price, rate limits, context,
  aliases, data handling), [Legal](https://docs.typesafe.ai/legal.md),
  [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
  (literal reading, counting, option order), [API](https://docs.typesafe.ai/api.md)
  (response fields). Read 2026-10-04.
- TypeSafe [Data Processing Agreement](https://typesafe.ai/legal/data-processing)
  and [Privacy Policy](https://typesafe.ai/legal/privacy-policy). Read 2026-10-04.
- OpenRouter [Data Collection](https://openrouter.ai/docs/guides/privacy/data-collection.md)
  and [Jev hub](https://openrouter.ai/docs/guides/community/jev.md). Read
  2026-10-04.
- Claude Sonnet 5.5 pricing: the claude-api skill's model table (cached
  2026-09-25) and its prompt-caching reference for cache multipliers.
- This repo: `typesafe-jev/cmd/evaluate/{call,config,fallback,tools,validation}.go`,
  `typesafe-jev/plugin/.mcp.json`, `typesafe-jev/plugin/mcp/claude.json`,
  `typesafe-jev/SECURITY.md`, `typesafe-jev/docs/provider-contracts.md`,
  `speckit-pro/speckit_pro_runner/research_broker.py`,
  `speckit-pro/speckit_pro_runner/research_preflight.py`,
  `docs/ai/specs/research-broker-contract.md`,
  `docs/ai/specs/harness-engineering-uplift-jev-catalog.md`,
  `speckit-pro/skills/speckit-coach/references/checklist-domains-guide.md`,
  `speckit-pro/skills/speckit-autopilot/references/consensus-protocol.md`.
- Issues: #1118, #1119, #1120, #1121, #1122, #1124, #1144, #1152.

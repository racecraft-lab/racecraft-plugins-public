# Checklist Domains Guide

How to identify and create effective domain checklists using the active host's
installed `speckit-checklist` command. Checklists are "unit tests for English" —
they validate the quality of your requirements, not the quality of your
implementation.

## The Core Concept: Unit Tests for Requirements

Checklists test whether your **specifications are complete, clear, and consistent** — not whether your code works.

| WRONG (tests implementation) | RIGHT (tests requirement quality) |
|---|---|
| "Verify the button clicks correctly" | "Are interaction requirements defined with expected outcomes?" |
| "Check API returns 200" | "Are success and error response schemas specified with examples?" |
| "Confirm dark mode works" | "Are visual requirements defined for both light and dark themes?" |
| "Test search returns results" | "Are relevance criteria measurable and threshold-defined?" |

---

## Spec-Driven Domain Recommendation

**Do not ask the developer to choose domains from a generic list.** Instead, analyze their spec and plan to recommend the most impactful domains automatically.

### Step 1: Extract Signals from Spec and Plan

Read `spec.md` and `plan.md` and identify which of these signal categories are present:

| Signal in Spec/Plan | Indicates Domain | Priority |
|---|---|---|
| API endpoints, REST routes, request/response schemas, HTTP methods | **api-contracts** | High when API work is central |
| User-facing UI, components, layouts, interactions, forms | **ux** | High for any frontend spec |
| Keyboard navigation, screen readers, ARIA, color contrast, WCAG | **accessibility** | High for public-facing UI |
| Authentication, authorization, tokens, secrets, user roles, input validation | **security** | High for any auth or data-handling spec |
| Response time budgets, caching, bundle size, query performance, concurrency | **performance** | Medium-High for API/data specs |
| Database schemas, migrations, validation rules, data consistency, transactions | **data-integrity** | High for any data model spec |
| LLM prompts, model calls, token limits, streaming, extraction, embeddings | **llm-integration** | High for any AI/ML spec |
| SSE, WebSocket, streaming protocols, real-time updates, event formats | **streaming-protocol** | High when streaming is core to the feature |
| Error handling, retry logic, fallbacks, circuit breakers, degradation | **error-handling** | Medium for complex integrations |
| State management, session handling, conversation history, caching strategy | **state-management** | Medium when state persistence matters |
| Third-party APIs, external services, webhooks, data imports | **integration** | Medium for specs with external dependencies |
| Touch targets, gestures, orientation, offline, responsive breakpoints | **mobile-ux** | High for mobile-first specs |
| Logging, monitoring, alerting, health checks, observability | **reliability** | Medium for production-critical specs |

### Step 2: Rank by Risk and Coverage Gap Potential

After extracting signals, rank the candidate domains:

1. **Core domains** (directly tied to the spec's primary deliverable) — always include
2. **Cross-cutting domains** (security, performance, error-handling) — include when the spec touches sensitive areas
3. **Edge domains** (reliability, mobile-ux) — include only when explicitly relevant

**Target: 2-4 domains per spec.** More than 4 is diminishing returns.

### Step 3: Generate Enriched Checklist Prompts

For each recommended domain, generate a prompt for the active host's
`speckit-checklist` command that includes **spec-specific focus areas** — not just
the bare domain name. The enriched prompt tells the checklist agent exactly what
to scrutinize.

**Pattern:**

```
speckit-checklist <domain-name>

Focus on <spec-name> requirements:
- <specific area 1 from the spec that this domain should validate>
- <specific area 2>
- <specific area 3>
- Pay special attention to: <the riskiest or most ambiguous part>
```

**Example — for a spec that defines a streaming chat API with LLM integration:**

```
speckit-checklist api-contracts

Focus on POST /chat endpoint requirements:
- Request model validation (message length, conversation_id format)
- SSE streaming response format (event types, field names, termination signal)
- Error response schemas (distinguish validation errors vs mid-stream errors)
- CORS headers for streaming (expose_headers for custom response headers)
- Pay special attention to: consistency between spec FR sections, data-model, and OpenAPI contract
```

### Step 4: Present Recommendations to the Developer

Present two to four domains with one sentence tying each to an observed risk or
coverage gap, then let the developer adjust them before any checklist is run.

## Quality Dimensions

Each checklist item should evaluate one of these requirement quality dimensions:

| Dimension | What It Checks |
|-----------|---------------|
| **Completeness** | Is anything missing from the requirement? |
| **Clarity** | Is the requirement unambiguous? Could two people interpret it differently? |
| **Consistency** | Does this requirement contradict any other requirement? |
| **Measurability** | Can you objectively verify whether this requirement is met? |
| **Scenario Coverage** | Are edge cases and error paths covered? |
| **Edge Cases** | Are boundary conditions defined (empty input, max values, concurrent access)? |

## Traceability Requirements

At least **80% of checklist items** must include a traceability reference:

| Marker | Meaning | Example |
|--------|---------|---------|
| `[Spec §X.Y]` | References a specific spec section | `[Spec §3.1]` Are request schemas defined? |
| `[Gap]` | Identifies missing requirement | `[Gap]` No rate limiting thresholds specified |
| `[Ambiguity]` | Flags unclear requirement | `[Ambiguity]` "Fast response" not quantified |
| `[Conflict]` | Notes contradicting requirements | `[Conflict]` §2.1 says sync, §3.1 says async |
| `[Assumption]` | Documents unstated assumption | `[Assumption]` Assumes single-region deployment |

## Addressing Gaps

When a checklist identifies `[Gap]` items:

1. Review whether the gap is a genuine missing requirement
2. Update `spec.md` or `plan.md` to address it
3. Re-run the checklist to verify coverage
4. If the gap is intentionally out of scope, document why

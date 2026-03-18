# Checklist Domains Guide

How to identify and create effective domain checklists using `/speckit.checklist`. Checklists are "unit tests for English" — they validate the quality of your requirements, not the quality of your implementation.

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
| API endpoints, REST routes, request/response schemas, HTTP methods | **api-contracts** | High — almost every spec needs this |
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

For each recommended domain, generate a `/speckit.checklist` prompt that includes **spec-specific focus areas** — not just the bare domain name. The enriched prompt tells the checklist agent exactly what to scrutinize.

**Pattern:**

```
/speckit.checklist <domain-name>

Focus on <spec-name> requirements:
- <specific area 1 from the spec that this domain should validate>
- <specific area 2>
- <specific area 3>
- Pay special attention to: <the riskiest or most ambiguous part>
```

**Example — for a spec that defines a streaming chat API with LLM integration:**

```
/speckit.checklist api-contracts

Focus on POST /chat endpoint requirements:
- Request model validation (message length, conversation_id format)
- SSE streaming response format (event types, field names, termination signal)
- Error response schemas (distinguish validation errors vs mid-stream errors)
- CORS headers for streaming (expose_headers for custom response headers)
- Pay special attention to: consistency between spec FR sections, data-model, and OpenAPI contract
```

```
/speckit.checklist llm-integration

Focus on Claude Agent SDK integration requirements:
- Prompt/system instruction specification (is routing logic documented?)
- Streaming event translation (SDK events → SSE protocol)
- Error handling for model-specific failures (throttling, context window, auth)
- Token efficiency and conversation context management
- Pay special attention to: what happens when the LLM returns unexpected output formats
```

```
/speckit.checklist streaming-protocol

Focus on Vercel AI SDK UIMessage Stream Protocol requirements:
- Complete event type catalog (text-delta, tool-call, tool-result, finish, error)
- Wire format specification (JSON field names, exact casing, required vs optional fields)
- Client disconnect handling and generator cleanup
- Relationship between streaming events and whitespace/empty content
- Pay special attention to: protocol version consistency across all artifacts (no v4/v5 mixing)
```

### Step 4: Present Recommendations to the Developer

Present the recommended domains with justification before running any checklists:

```markdown
Based on your spec, I recommend these domain checklists:

1. **api-contracts** — Your spec defines 3 endpoints with Pydantic models,
   streaming responses, and custom headers. High risk for inconsistencies
   between spec, data-model, and contract artifacts.

2. **llm-integration** — Your spec integrates Claude via Agent SDK with
   prompt-based routing. The routing criteria and error handling for
   LLM-specific failures need validation.

3. **streaming-protocol** — SSE streaming is core to the feature. The
   event format, termination signal, and header requirements need
   cross-artifact consistency checks.

Shall I run these, or would you like to adjust the domains?
```

---

## Domain Reference Catalog

### API Contracts
Validates: Endpoint consistency, request/response schemas, error structures, streaming format, rate limiting, versioning, authentication.

**When the spec mentions:** endpoints, routes, REST, HTTP methods, request/response models, Pydantic, JSON Schema, OpenAPI, status codes, headers, content types.

Example items:
- `[Spec §3.1]` Are all endpoint request schemas defined with typed models?
- `[Spec §3.4]` Are error response structures consistent across all endpoints?
- `[Gap]` Are rate limiting thresholds specified per endpoint?

### UX
Validates: User flows, interaction patterns, loading states, error states, visual hierarchy, responsive behavior.

**When the spec mentions:** UI components, layouts, forms, buttons, modals, drawers, navigation, user interactions, visual design, responsive breakpoints.

Example items:
- `[Spec §2.1]` Are loading states defined for all async operations?
- `[Gap]` Are empty/zero-state requirements specified?
- `[Ambiguity]` Is "prominent display" quantified with specific sizing/positioning?

### Accessibility
Validates: Keyboard navigation, screen reader support, ARIA attributes, color contrast, focus management, touch targets.

**When the spec mentions:** keyboard navigation, screen readers, ARIA, WCAG, color contrast, focus management, or any public-facing UI that must meet accessibility standards.

Example items:
- `[Spec §2.5]` Are keyboard navigation paths specified for all interactive elements?
- `[Ambiguity]` Are focus management requirements defined for modal dialogs?
- `[Gap]` Are ARIA role and label requirements documented for custom components?

### Security
Validates: Authentication, authorization, input validation, data encryption, secrets management, OWASP top 10.

**When the spec mentions:** auth, tokens, API keys, user roles, permissions, input validation, encryption, secrets, credentials, CORS, CSP, sanitization.

Example items:
- `[Spec §4.1]` Are authentication requirements specified with supported methods?
- `[Gap]` Are input validation rules defined for all user-facing fields?
- `[Spec §4.3]` Are secrets management requirements defined (no hardcoded credentials)?

### Performance
Validates: Response time budgets, bundle size limits, caching strategy, database query limits, concurrency.

**When the spec mentions:** latency, response time, caching, TTL, bundle size, query performance, pagination, concurrency, throttling, rate limits.

Example items:
- `[Spec §5.1]` Are response time budgets defined per endpoint (e.g., p95 < 200ms)?
- `[Gap]` Are bundle size budgets specified for frontend builds?
- `[Spec §5.3]` Are caching strategies defined with TTL and invalidation rules?

### Data Integrity
Validates: Schema definitions, validation rules, migration strategy, backup/recovery, consistency constraints.

**When the spec mentions:** database schemas, migrations, data models, validation, constraints, transactions, foreign keys, indexes, data consistency.

Example items:
- `[Spec §6.1]` Are all data model fields typed with constraints?
- `[Gap]` Are migration rollback requirements specified?
- `[Ambiguity]` Are cascade delete behaviors explicitly defined?

### LLM Integration
Validates: Prompt design, extraction accuracy, error handling, streaming behavior, token efficiency, model fallbacks.

**When the spec mentions:** LLM, AI model, prompts, system instructions, embeddings, tokens, context window, model routing, extraction, Claude, GPT, Bedrock.

Example items:
- `[Spec §7.1]` Are prompt/system instructions specified or referenced?
- `[Gap]` Are fallback behaviors defined for model-specific failures?
- `[Ambiguity]` Are extraction accuracy criteria measurable?

### Streaming Protocol
Validates: Event format consistency, wire protocol, termination signals, reconnection, backpressure, client disconnect handling.

**When the spec mentions:** SSE, WebSocket, streaming, event-stream, real-time, Server-Sent Events, event types, streaming protocol.

Example items:
- `[Spec §3.5]` Are all event types in the streaming protocol cataloged with exact field names?
- `[Gap]` Is client disconnect / generator cleanup behavior specified?
- `[Conflict]` Are protocol version references consistent across all artifacts?

### Error Handling
Validates: Error classification, recovery paths, retry logic, fallback behavior, user-facing error messages, degradation strategy.

**When the spec mentions:** error handling, retries, fallbacks, circuit breakers, degradation, error messages, failure modes, recovery.

Example items:
- `[Spec §8.1]` Are all failure modes classified with expected behavior?
- `[Gap]` Are retry/timeout requirements defined for external dependencies?
- `[Ambiguity]` Are user-facing error messages specified or pass-through?

### State Management
Validates: State lifecycle, persistence strategy, session handling, cache invalidation, concurrent access.

**When the spec mentions:** state, sessions, conversation history, caching, in-memory, persistence, TTL, concurrent access, cleanup.

Example items:
- `[Spec §9.1]` Are state lifecycle requirements (creation, TTL, cleanup) specified?
- `[Gap]` Are concurrent access requirements defined?
- `[Ambiguity]` Is the persistence strategy (in-memory vs durable) explicitly chosen?

### Integration
Validates: External service contracts, authentication, rate limits, data format compatibility, timeout handling.

**When the spec mentions:** third-party APIs, external services, webhooks, imports, SDK clients, service dependencies.

Example items:
- `[Gap]` Are external service SLAs and timeout requirements documented?
- `[Spec §10.1]` Are data format compatibility requirements specified?
- `[Assumption]` Is the assumption of external service availability validated?

### Mobile UX
Validates: Touch targets (48px minimum), gestures, orientation, offline behavior, push notifications, responsive design.

**When the spec mentions:** mobile, touch, gestures, orientation, offline, responsive, breakpoints, native, push notifications.

### Reliability / Observability
Validates: Logging, monitoring, alerting, health checks, circuit breakers, graceful degradation.

**When the spec mentions:** logging, monitoring, alerts, health checks, uptime, SLA, observability, metrics, tracing.

---

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

## Tips

- Run checklists **after plan** (not after specify) — you need both spec and plan context
- Run **2-4 domain checklists** per feature — more than 4 is diminishing returns
- Each `/speckit.checklist` run creates a NEW file — you can iterate safely
- Short descriptive file names: `ux.md`, `api.md`, `security.md`, `performance.md`
- Focus on domains where your project has the most risk or complexity
- **Always generate enriched prompts** — a bare `/speckit.checklist security` is far less effective than one that lists the specific security-relevant areas from the spec

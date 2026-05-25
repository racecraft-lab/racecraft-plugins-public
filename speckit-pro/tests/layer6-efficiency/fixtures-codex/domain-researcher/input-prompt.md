## Clarify Question

**Spec:** SPEC-009 (search and database access)

**Question:** When a cursor-based paginated list endpoint returns the
last page of results, what is the industry-standard convention for
signaling "no more results" to the caller — and where should the
documentation point readers for the formal specification of that
convention?

**Context from spec.md:**
> The system MUST expose a cursor-based `list_tasks` endpoint. The spec
> does not currently state what value `next_cursor` takes on the final
> page, nor whether a `has_more` boolean is expected by callers
> following common pagination conventions.

The question is being routed to you as the domain researcher because
this is about industry standards and external API conventions, not
about how the codebase or project specs handle it today.

## What we need from you

Answer the question from the perspective of established external
conventions: well-known API design guides (Google, Stripe, GitHub),
RFCs, and community patterns. Cite the specific public documentation
that prescribes the convention. Confidence should reflect how widely
the convention is adopted across major API providers — a convention
backed by multiple providers is "high"; one backed by a single provider
is "medium".
